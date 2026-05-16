import asyncio
import os
import platform
import tempfile
from pathlib import Path

if platform.system() == "Windows":
    import msvcrt
else:
    import fcntl


class GlobalLock:
    def __init__(
            self,
            name: str,
            lock_time: int = 5,
            try_times: int = 3,
            _retry_interval: float = 0.3
    ):
        """
        Args
        ----
        name: 锁的名称，决定加锁颗粒度
        lock_time: 锁定时间，单位秒 (暂时未使用，文件锁会在进程退出时自动释放)
        try_times: 加锁失败时，自旋次数
        _retry_interval: 加锁失败重试时，时间间隔，单位秒
        """
        self.name = name
        self.lock_time = lock_time
        self.try_times = try_times
        self._retry_interval = _retry_interval
        self.lock_file_path = None
        self.lock_fd = None
        self._locked = False

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return None

    @property
    def locked(self) -> bool:
        return self._locked

    async def acquire(self):
        """尝试获取锁"""
        # 创建锁文件路径 (使用临时目录确保跨平台兼容性)
        temp_dir = Path(tempfile.gettempdir())
        # 使用锁名称生成安全的文件名
        safe_name = "".join(c for c in self.name if c.isalnum() or c in "._- ")
        self.lock_file_path = temp_dir / f"global_lock_{safe_name}.lock"

        for attempt in range(self.try_times):
            try:
                # 尝试获取锁
                if self._try_acquire():
                    self._locked = True
                    return True
            except Exception:
                pass

            # 如果是最后一次尝试，不再等待
            if attempt == self.try_times - 1:
                break

            # 等待重试
            await asyncio.sleep(self._retry_interval)

        self._locked = False
        return False

    def _try_acquire(self):
        """尝试获取文件锁"""
        try:
            # 以读写模式打开锁文件，如果不存在则创建
            flags = os.O_CREAT | os.O_RDWR
            if platform.system() != "Windows":
                flags |= os.O_TRUNC  # Unix-like系统截断文件

            self.lock_fd = os.open(str(self.lock_file_path), flags)

            # 根据平台使用不同的文件锁机制
            if platform.system() == "Windows":
                # Windows 平台使用 msvcrt.locking
                msvcrt.locking(self.lock_fd, msvcrt.LK_NBLCK, 1)  # 非阻塞锁
            else:
                # Unix-like 平台使用 fcntl.flock
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # 排他非阻塞锁

            # 锁定成功，写入当前进程ID以便调试（可选）
            pid = os.getpid()
            os.write(self.lock_fd, str(pid).encode('utf-8'))
            os.ftruncate(self.lock_fd, len(str(pid)))  # 截断到PID长度避免残留数据

            return True
        except (IOError, OSError, BlockingIOError):
            # 锁已被其他进程占用，清理并返回False
            if self.lock_fd is not None:
                try:
                    os.close(self.lock_fd)
                except OSError:
                    pass
                self.lock_fd = None
            return False

    def release(self):
        """释放锁"""
        if self.lock_fd is not None:
            try:
                # 根据平台释放锁
                if platform.system() == "Windows":
                    # Windows上解锁
                    os.lseek(self.lock_fd, 0, os.SEEK_SET)
                    msvcrt.locking(self.lock_fd, msvcrt.LK_UNLCK, 1)
                else:
                    # Unix-like系统解锁
                    fcntl.flock(self.lock_fd, fcntl.LOCK_UN)

                # 关闭文件描述符
                os.close(self.lock_fd)
                self.lock_fd = None
                self._locked = False

                # 删除锁文件（可选，但推荐删除以保持整洁）
                try:
                    os.unlink(str(self.lock_file_path))
                except OSError:
                    pass  # 文件可能已被其他进程删除
            except Exception:
                # 发生异常也要确保清理资源
                try:
                    os.close(self.lock_fd)
                except OSError:
                    pass
                self.lock_fd = None
                self._locked = False
