$.cl = {
    jstreeTypes: {
        bin: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/bin.svg"},
        img: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/img.svg"},
        text: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/txt.svg"},
        md: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/md.svg"},
        folder: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/folder.png"},
        default: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/folder.png"}
    },
    preventDefault: function (e){e.preventDefault()},
    windowSizeMonitor: function (){
        if(document.documentElement.clientWidth < 605){
            $("#browser-prompt, #nav, #content").css({"display": "none"});
            $("#uavaliable-mask").css({"display": "block"});
        }else{
            let splitLineWidth = 6,
                treeW = parseFloat($("#folder-tree").css("width").replace("px", "")),
                editW = parseFloat($("#input-area").css("width").replace("px", ""));

            // -1 阻止浮点数原因，导致实际宽度多出1像素造文档栏挤压出界
            let showW = document.body.offsetWidth - splitLineWidth*2 - treeW - editW - 1;
            $("#content-area").css({width: showW + 'px'});
            $("#nav, #content").css({"display": "block"});
            $("#browser-prompt, #uavaliable-mask").css({"display": "none"});
            $.cl.compatibilityChecking();
        }
    },
    initPageSplitWidth: function () {
        let windowWidth = document.body.offsetWidth,
            splitLineWidth = 6;
        let treeW = Math.max(windowWidth*0.2, 220);
        let contentW = (windowWidth - treeW - splitLineWidth*2) / 2 - 1;
        $("#folder-tree").css({width: treeW + "px"});
        $("#input-area").css({width: contentW + "px"});
        $("#content-area").css({width: contentW + "px"});

        $.cl.setSplitLineAction();
    },
    setSplitLineAction: function () {
        let lSpLine = document.getElementById('left-split-line'),
            rSpLine = document.getElementById('right-split-line'),
            startX = 0,
            startWidth = 0,
            leftDown,
            ldOrigin,
            rdOrigin;

        lSpLine.addEventListener('mousedown', (event) => {onMouseDown(event, true)});
        rSpLine.addEventListener('mousedown', (event) => {onMouseDown(event, false)});

        function onMouseDown(event, isLeftBar) {
            console.log("this event!", event, ", isLeftBar: ", isLeftBar);
            leftDown = isLeftBar;
            startX = event.clientX;
            startWidth = parseInt(document.defaultView.getComputedStyle(isLeftBar === true ? lSpLine : rSpLine).width, 10);
            ldOrigin = parseFloat($(isLeftBar ? "#folder-tree" : "#input-area").css("width").replace("px", ""));
            rdOrigin = parseFloat($(isLeftBar ? "#input-area" : "#content-area").css("width").replace("px", ""));
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        }

        function onMouseMove(event) {
            let width = startWidth + event.clientX - startX;
            let lD, rD;
            if (leftDown) {
                lD = $("#folder-tree");
                rD = $("#input-area");
            } else {
                lD = $("#input-area");
                rD = $("#content-area");
            }
            let lW = ldOrigin + width,
                rW = rdOrigin - width;
            if (lW < 100 || rW < 100){
                return;
            }
            lD.css({width: lW + 'px'});
            rD.css({width: rW + 'px'});
        }

        function onMouseUp(event) {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }
    },
    popupedMessageBoxId: undefined,
    popupMessage: function (msg, title, timeout){
        var promptModal = $(".cl-prompt");
        if(promptModal.css("opacity") > 0){
            $.cl.clearMessage();
            setTimeout(function(){
                $.cl.popupMessage(msg, title, timeout)
            }, 200);
        }else{
            if(timeout > 0){
                if($.cl.popupedMessageBoxId){
                    clearInterval($.cl.popupedMessageBoxId);
                    $.cl.popupedMessageBoxId = undefined;
                }
                $(".cl-prompt-clock").css({display: "block"}).find("span").html(timeout);
                $.cl.popupedMessageBoxId = setInterval(function(){
                    var clPromptClockTimeOutDom = $(".cl-prompt-clock span");
                    var timeout = parseInt(clPromptClockTimeOutDom.html()) - 1;
                    clPromptClockTimeOutDom.html(timeout);
                    if(timeout <= 0){
                        $.cl.clearMessage();
                        clearInterval($.cl.popupedMessageBoxId);
                        $.cl.popupedMessageBoxId = undefined;
                    }
                }, 1000)
            }else{
                $(".cl-prompt-clock").css({display: "none"})
            }
            $("#cl-prompt-title").html(title || "提示");
            $("#cl-prompt-content").html(msg);
            promptModal.css({"opacity": "1", "top": "20px", "z-index": "10"}).children().eq(1).off("click").click($.cl.clearMessage);
        }
    },
    clearMessage: function (){
        if($.cl.popupedMessageBoxId){
            clearInterval($.cl.popupedMessageBoxId);
            $.cl.popupedMessageBoxId = undefined;
        }
        $(".cl-prompt").css({"opacity": "0", "top": "0px", "z-index": "-10"});
    },
    popupConfirm: function (msg, callback, cancelback, title){
        $("#cl-confirm-title").html(title || "提示");
        $("#cl-confirm-body").html(msg);
        $("#cl-confirm-cnf-btn").off("click").click(function(){
            $("#cl-confirm").modal("hide");
            try{
                callback();
            }catch (e){}
        });
        $("#cl-confirm-ccl-btn").css({"display": cancelback === false ? "none" : "initial"}).off("click").click(function(){
            $("#cl-confirm").modal("hide");
            try{
                cancelback();
            }catch (e){}
        });
        $("#cl-confirm").modal("show");
    },
    onLoginOrRegistered: function (data){
        if(data.code !== 0){
            var msg = "操作失败。详细信息：" + data.msg;
            $.cl.popupMessage(msg);
            return ;
        }
        window.contextData.loginInfo = {email: data.email};
        $.cl.renderLoginPage();
    },
    saveBtnAnimationId: undefined,
    drawSaveBtnInitState: function () {
        if ($.cl.saveBtnAnimationId !== undefined) {
            clearTimeout($.cl.saveBtnAnimationId);
            $.cl.saveBtnAnimationId = undefined;
        }
        $("#save-btn").html('<i class="fa fa-save" aria-hidden="true"></i> 保存');
    },
    drawSavingAnimation: function () {
        if ($.cl.saveBtnAnimationId !== undefined) {
            clearTimeout($.cl.saveBtnAnimationId);
            $.cl.saveBtnAnimationId = undefined;
        }
        $("#save-btn").html('<i class="fa fa-spin fa-adjust" aria-hidden="true"></i> 保存中');
    },
    drawSaveSuccessAnimation: function () {
        $("#save-btn").html('<i class="fa fa-check-circle-o" aria-hidden="true"></i> 已保存');
        if ($.cl.saveBtnAnimationId !== undefined) {
            clearTimeout($.cl.saveBtnAnimationId);
        }
        $.cl.saveBtnAnimationId = setTimeout($.cl.drawSaveBtnInitState, 2500);
    },
    onSaveContent: false,
    lastCommitMd5: undefined,
    onOpenFile: false,
    sendRequest: function (data, callback, fallback){
        fallback = fallback || function(){$.cl.popupMessage("操作失败，请检查你的网络连接。")};

        $.ajax({
            url: "/notebook/api",
            type: "post",
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify(data),
            success: function (data){
                callback(data);
            },
            error: function (data) {
                fallback(data);
            }
        });
    },
    register: function (){
        var email = $("input[name=email]").val(),
            password = $("input[name=password]").val();
        if(email.length < 1 || password.length > 32 || password.length < 5){
            $.cl.popupMessage("请输入正确的邮箱和密码。");
            return ;
        }
        $.cl.sendRequest({action: "register", email: email, password: password}, $.cl.onLoginOrRegistered);
    },
    login: function (){
        var email = $("input[name=email]").val(),
            password = $("input[name=password]").val();
        if(email.length < 1 || password.length > 32 || password.length < 5){
            $.cl.popupMessage("请输入正确的邮箱和密码。");
            return ;
        }
        $.cl.sendRequest({action: "login", email: email, password: password}, $.cl.onLoginOrRegistered);
    },
    logout: function (){
        var afterLogOut = function (data){
            if(data.code !== 0){
                var msg = "操作失败。详细信息：" + data.msg;
                $.cl.popupMessage(msg);
                return ;
            }
            window.contextData.loginInfo = false;
            $.cl.renderCurrentEditDocumentTitle();
            $.cl.renderUnloginPage();
        };
        $.cl.sendRequest({action: "logout"}, afterLogOut);
    },
    showChangePasswordDialog: function () {
        var onConfirmBtnClicked = function (){
            $("#input-modal").modal("hide");
            var oldPassword = $("input[name=old-passwd]").val(),
                newPassword = $("input[name=new-passwd]").val(),
                newPassword2 = $("input[name=confirm-new-passwd]").val();

            /* check old password */
            if (oldPassword.length > 32 || oldPassword.length < 5){
                $.cl.popupMessage("修改失败：请正确输入密码！");
                return false;
            }
            if (newPassword.length > 32 || newPassword.length < 5){
                $.cl.popupMessage("修改失败：新密码长度超出范围，请确保6~32个字符之间！");
                return false;
            }
            if (newPassword !== newPassword2){
                $.cl.popupMessage("修改失败：新密码输入不一致！");
                return false;
            }
            if (oldPassword === newPassword){
                $.cl.popupMessage("修改失败：新密码与旧密码相同！");
                return false;
            }

            var onChangePasswordResponsed = function (data){
                if(data.code === 0){
                    $.cl.popupMessage("修改成功！请重新登录！", null, 3);
                    $.cl.renderUnloginPage();
                }else{
                    $.cl.popupMessage("修改失败：" + (data.msg || "未知原因"));
                }
            };
            $.cl.sendRequest(
                {action: "change_password", old_password: oldPassword, new_password: newPassword},
                onChangePasswordResponsed
            )
        };
        $("#input-modal-confirm-btn").off("click").click(onConfirmBtnClicked);
        $("#input-modal-title").html("更改密码");
        $("#input-modal-body").html([
            '<label>旧的密码: <input class="redinput" name="old-passwd" type="password"/></label><br/>',
            '<label style="margin-top: 15px">新的密码: <input class="redinput" name="new-passwd" type="password"/></label>',
            '<label>再次确认: <input class="redinput" name="confirm-new-passwd" type="password"/></label>'
        ].join(""));
        $("input[name=confirm-new-passwd]").keyup(function(e){if(e.keyCode === 13)$("#input-modal-confirm-btn").trigger("click");});
        $("#input-modal").modal("show");
    },

    docBaseContent: "",
    getCurrentDoc: function () {
        let ver = parseInt(localStorage.docVer),
            bs = parseInt(localStorage.docBase);
        return {
            path: localStorage.docPath,
            version: isNaN(ver) ? undefined : ver,
            base: isNaN(bs) ? undefined : bs,
            baseContent: $.cl.docBaseContent,
        }
    },
    setCurrentDoc: function (option) {
        // 如果设置其他项，则 path 保持
        // 如果设置 path 而未指定 ver 和 content, 则清空后者
        if (option.path !== undefined) {
            localStorage.docPath = option.path;
        }
        localStorage.docVer = option.version;
        if (option.base !== undefined) {
            localStorage.docBase = option.base;
        }
        if (option.baseContent !== undefined) {
            $.cl.docBaseContent = option.baseContent;
        }
    },
    clearCurrentDoc: function () {
        localStorage.removeItem("docPath");
        localStorage.docVer = undefined;
        localStorage.docBase = undefined;
        $.cl.docBaseContent = "";
        $.cl.lastSavedContent = undefined;
    },
    jstNodeOpenCb: {}, // nodeId -> [function (node) {}]
    registerJstNodeOpenCb: function (nodeId, cb) {
        if (nodeId in $.cl.jstNodeOpenCb) {
            $.cl.jstNodeOpenCb[nodeId].push(cb);
        } else {
            $.cl.jstNodeOpenCb[nodeId] = [cb];
        }
    },
    onJstreeNodeOpen: function (e, node) {
        if (node.id in $.cl.jstNodeOpenCb) {
            for (let j = 0; j < $.cl.jstNodeOpenCb[node.id].length; j++) {
                let cb = $.cl.jstNodeOpenCb[node.id].pop();
                cb(node);
            }
        }
    },

    openJstreeNode: function (nodeId){
        // nodeId 如 "/VVV/a.md"
        let jst = $("#jstree").jstree();

        // 从根节点往叶子节点寻找，如果是展开的，则往叶子节点寻找，否则展开此节点

        let searchNode = jst.get_node("/");
        let toOpen = undefined;

        while (searchNode !== undefined) {
            if (searchNode.state.opened === false) {
                toOpen = searchNode;
                break;
            }
            let nextLoop = undefined;
            for (const child of searchNode.children) {
                let childNode = jst.get_node(child)
                if (childNode.type === "folder" && nodeId.indexOf(childNode.id + "/") >= 0) {
                    // 找到了要展开的孩子
                    nextLoop = childNode
                    break;
                }
            }
            searchNode = nextLoop;  // 下一轮次继续搜索
        }
        if (toOpen === undefined) {
            $("#jstree").jstree('select_node', nodeId);
            return;
        }
        // 注册回调，展开这个节点
        $.cl.registerJstNodeOpenCb(toOpen.id, (node) => {
            $.cl.openJstreeNode(nodeId);
        })
        jst.open_node(toOpen.id);
    },
    showMkdirDialog: function(nodeId){
        var onMkdirDialogConfirmBtnClicked = function (){
            $("#input-modal").modal("hide");
            var nodeId = $(this).data("nodeId"),
                dirName = $("input[name=folder-name]").val();
            if (!dirName.match(/^[\.a-zA-Z0-9_\u4e00-\u9fa5]+$/)){
                $.cl.popupConfirm("文件名仅允许包含数字、字母、下划线以及汉字，不支持其它字符。请返回修改。", null, false, "文件名有误");
                return;
            }
            var onMkdirResponsed = function (data){
                if(data.code === 0){
                    $.cl.popupMessage("创建成功！", null, 3);
                    let jst = $("#jstree").jstree(),
                        toOpen = (nodeId === "/" ? "" : nodeId) + "/" + dirName;
                    jst.refresh_node(nodeId);

                    function openThisNode(leftTimes) {
                        let node = jst.get_node(toOpen);
                        if (node === false && leftTimes > 0) {
                            console.log("next loop");
                            setTimeout(function (){openThisNode(leftTimes - 1)}, 100);
                            return;
                        }
                        if (node.state.opened) {
                            console.log("this node opened: ", toOpen);
                            return;
                        }
                        $.cl.openJstreeNode(toOpen);
                    }
                    openThisNode(5);
                }else{
                    $.cl.popupMessage("创建失败：" + data.msg);
                }
            };
            $.cl.sendRequest({action: "mkdir", node_id: nodeId, dir_name: dirName}, onMkdirResponsed)
        };
        $("#input-modal-confirm-btn").data("nodeId", nodeId).off("click").click(onMkdirDialogConfirmBtnClicked);
        $("#input-modal-title").html("新建文件夹");
        $("#input-modal-body").html('<label>新的文件夹名称: <input class="redinput" type="text" name="folder-name"/></label>');
        $("input[name=folder-name]").keyup(function(e){if(e.keyCode === 13)$("#input-modal-confirm-btn").trigger("click");});
        $("#input-modal").modal("show");
    },
    showDeleteConfirmDialog: function(nodeId){
        $("#input-modal-confirm-btn").data("nodeId", nodeId).off("click").click(function(){
            // 删除按钮按下之后
            $("#input-modal").modal("hide");

            let inputDelNode = $("input[name=del-obj-name]").val();
            if (inputDelNode !== nodeId) {
                $.cl.popupMessage("输入错误，删除取消。", "", 2);
                return;
            }

            $.cl.sendRequest({action: "rm", node_id: nodeId}, function (data){
                // 删除成功之后
                if(data.code === 0){
                    $.cl.popupMessage("删除成功！", null, 3);
                    let refreshNode = nodeId.split("/").slice(0, -1).join("/") || "/";
                    $("#jstree").jstree().refresh_node(refreshNode);
                    if(nodeId === $.cl.getCurrentDoc().path){
                        $.cl.setCurrentDoc({"path": ""})
                        $.cl.renderCurrentEditDocumentTitle();
                    }
                }else{
                    $.cl.popupMessage("删除失败：" + data.msg);
                }
            })
        });

        $("#input-modal-title").html("删除");
        $("#input-modal-body").html(
            '删除之后不可恢复！<br/>如果您确定，请在下方输入"' + nodeId + '"</br></br>' +
            '<label>删除: <input class="redinput" type="text" name="del-obj-name"/></label>'
        );
        $("input[name=del-obj-name]").keyup(function(e){if(e.keyCode === 13)$("#input-modal-confirm-btn").trigger("click");});
        $("#input-modal").modal("show");
    },
    showRenameDialog: function (nodeId, isdir){
        var onConfirmBtnClicked = function (){
            $("#input-modal").modal("hide");
            var nodeId = $(this).data("nodeId"),
                dirName = $("input[name=folder-name]").val();
            if (!dirName.match(/^[\.a-zA-Z0-9_\u4e00-\u9fa5]+$/)){
                $.cl.popupConfirm("仅允许包含数字、字母、下划线以及汉字，不支持其它字符。请返回修改。", null, false, "名称有误");
                return false;
            }
            var onRenameResponse = function (data){
                if(data.code === 0){
                    $.cl.popupMessage("重命名成功！", null, 3);
                    var nodePath = nodeId.split("/").slice(0, -1).join("/") || "/";
                    $("#jstree").jstree().refresh_node(nodePath);
                    if (nodeId === $.cl.getCurrentDoc().path){
                        $.cl.setCurrentDoc({path: (nodePath === "/" ? "" : nodePath) + "/" + dirName})
                        $.cl.renderCurrentEditDocumentTitle();
                    }
                }else{
                    $.cl.popupMessage("重命名失败：" + data.msg);
                }
            };
            $.cl.sendRequest({action: "rename", node_id: nodeId, new_name: dirName}, onRenameResponse);
        };
        $("#input-modal-confirm-btn").data("nodeId", nodeId).off("click").click(onConfirmBtnClicked);
        $("#input-modal-title").html(isdir ? "重命名文件夹" : "重命名文件");
        $("#input-modal-body").html([
            '<p style="text-align: center">将“' + nodeId.split("/").slice(-1) + '”重新命名。</p>',
            '<label>新的名称: <input class="redinput" type="text" name="folder-name"/></label>'
        ].join(""));
        $("input[name=folder-name]").keyup(function(e){if(e.keyCode === 13)$("#input-modal-confirm-btn").trigger("click");});
        $("#input-modal").modal("show");
    },
    showNewFileDialog: function (nodeId){
        var onConfirmBtnClicked = function (){
            $("#input-modal").modal("hide");
            var nodeId = $(this).data("nodeId"),
                fileName = $("input[name=folder-name]").val();
            if (!fileName.match(/^[\.a-zA-Z0-9_\u4e00-\u9fa5]+$/)){
                $.cl.popupConfirm("仅允许包含数字、字母、下划线以及汉字，不支持其它字符。请返回修改。", null, false, "名称有误");
                return false;
            }
            var onNewFileResponse = function (data){
                if(data.code === 0){
                    let jst = $("#jstree").jstree(),
                        createdFile = (nodeId === "/" ? "" : nodeId) + "/" + fileName;
                    $.cl.popupMessage("创建成功：" + createdFile, null, 3);
                    jst.refresh_node(nodeId);

                    let curDoc = $.cl.getCurrentDoc();
                    if (curDoc.path === undefined || curDoc.path.length === 0) {
                        $.cl.openFile(createdFile);
                    }
                }else{
                    $.cl.popupMessage("创建失败：" + data.msg);
                }
            };
            $.cl.sendRequest({action: "new", node_id: nodeId, file_name: fileName}, onNewFileResponse);
        };
        $("#input-modal-confirm-btn").data("nodeId", nodeId).off("click").click(onConfirmBtnClicked);
        $("#input-modal-title").html("新建文件");
        $("#input-modal-body").html([
            '<p>新建一个文档。系统根据文件扩展名判断文件类型，如果你填写二进制文件的文件类型，将不能对该文件进行编辑。',
            '这是一个示例： readme.md 。',
            '</p>',
            '<label>新的文件名: <input class="redinput" type="text" name="folder-name"/></label>'
        ].join(""));
        $("input[name=folder-name]").keyup(function(e){if(e.keyCode === 13)$("#input-modal-confirm-btn").trigger("click");});
        $("#input-modal").modal("show");
    },
    renderCurrentEditDocumentTitle: function (){
        let curDoc = $.cl.getCurrentDoc();
        if(curDoc.path !== undefined && curDoc.path.length > 0){
            var jstreeInstence = $("#jstree").jstree();
            jstreeInstence.deselect_all();
            jstreeInstence.select_node(curDoc.path);
            $("#input-text-area").prev().html("编辑 - " + curDoc.path);
        }else{
            $("#input-text-area").prev().html("编辑");
            document.getElementById('input-text-area').value = "";
        }
    },
    showSaveContentDialog: function (path, content){
        // TODO：保存新文件
        var onConfirmBtnClicked = function (){
            $("#input-modal").modal("hide");

            var nodeId = $(this).data("nodeId"),
                content = $(this).data("content"),
                fileName = $("input[name=folder-name]").val();

            if (!fileName.match(/^[\.a-zA-Z0-9_\u4e00-\u9fa5]+$/)){
                $.cl.popupConfirm("仅允许包含数字、字母、下划线以及汉字，不支持其它字符。请返回修改。", null, false, "名称有误");
                return false;
            }

            var onSaveContentResponsed = function (data){
                if(data.code === 0){
                    $.cl.popupMessage("保存成功！", null, 3);
                    $("#jstree").jstree().refresh_node(nodeId);
                }else{
                    $.cl.popupMessage("保存失败：" + data.msg);
                }
                $.cl.setCurrentDoc({path: nodeId + "/" + fileName});
                $.cl.renderCurrentEditDocumentTitle();
            };
            $.cl.sendRequest({action: "save", node_id: nodeId + "/" + fileName, content: encodeURIComponent(content)}, onSaveContentResponsed);
        };
        $("#input-modal-confirm-btn").data("nodeId", path).data("content", content).off("click").click(onConfirmBtnClicked);
        $("#input-modal-title").html("保存文档到你的目录中");
        $("#input-modal-body").html([
            '<p>将你编辑的文档保存到“<strong>' + path + '/”</strong>下。</p>',
            '<p>这个路径可能是系统默认的，但如果你想改变存放的地方，请在左侧的目录结构中点击你想保存的位置，然后再按下“Ctrl”和“S”键。</p>',
            '<label>文件名: <input class="redinput" type="text" name="folder-name"/></label>'
        ].join(""));
        $("input[name=folder-name]").keyup(function(e){if(e.keyCode === 13)$("#input-modal-confirm-btn").trigger("click");});
        $("#input-modal").modal("show");
    },
    openFile: function (nodeId){
        if ($.cl.onOpenFile){
            $.cl.popupMessage("正在加载，请稍候。", undefined, 3);
            return;
        }else{
            $.cl.onOpenFile = true;
        }

        $("#input-text-area").prev().html("正在加载...");
        var onFileOpenedResponse = function (data){
            $.cl.onOpenFile = false;
            if (data.code !== 0){
                var msg = "操作失败。详细信息：" + data.msg;
                $.cl.popupMessage(msg);
                $.cl.clearCurrentDoc();
                $.cl.renderCurrentEditDocumentTitle();
                return ;
            }
            if (data.img === true) {
                // 预览图片，渲染dom
                document.getElementById('input-text-area').value = '![](' + data.url + ')';
                $.cl.clearCurrentDoc();
                $.cl.setCurrentDoc({path: nodeId});
                $.cl.renderCurrentEditDocumentTitle();
                return;
            }
            let baseContent = data.base_content,
                diff = data.diff,
                resultContents = [],
                index = 0,
                renderContent = "";
            if (diff.length === 0) {
                renderContent = baseContent;
            } else {
                for (let i = 0; i < diff.length; i++) {
                    let d = diff[i];
                    if (d.added === true) {
                        resultContents.push(d.value);
                    } else if (d.removed === true) {
                        index += d.count;
                    } else {
                        resultContents.push(baseContent.substring(index, index + d.count));
                        index += d.count;
                    }
                }
                resultContents.push(baseContent.substring(index))
                renderContent = resultContents.join("");
            }
            $.cl.clearCurrentDoc();
            $.cl.setCurrentDoc({path: nodeId, version: data.version, base: data.base, baseContent: baseContent});
            $.cl.renderCurrentEditDocumentTitle();
            document.getElementById('input-text-area').value = renderContent;
        };
        var onOpenFileFailed = function (e){
            $.cl.onOpenFile = false;
            $.cl.popupMessage("操作失败，请检查你的网络连接。")
        };
        $.cl.sendRequest({action: "open", "node_id": nodeId}, onFileOpenedResponse, onOpenFileFailed);
    },
    shareFile: function(nodeId){
        $.cl.sendRequest({action: "share", node_id: nodeId}, function (data){
            if (data.code !== 0){
                var msg = "操作失败。详细信息：" + data.msg;
                $.cl.popupMessage(msg);
                return ;
            }
            var new_url = window.location.protocol + "//" + window.location.host + data.key;
            $.cl.popupConfirm(
                '<p>此文件的分享链接已经生成：<br />' + new_url + '<br />在新的标签页打开吗？</p>',
                function(){window.open(new_url)}
            );
        })
    },
    renderJstreeContextMenu: function(node){
        var selectedNodeId = node.id;
        if (node.type !== "folder") {
            return {
                "open": {
                    "label": "打开",
                    "action": function () {
                        if(
                            node.type === "text"
                            || node.type === "md"
                            || node.type.toLowerCase() === "png"
                            || node.type.toLowerCase() === "jpg"
                            || node.type.toLowerCase() === "jpeg"
                            || node.type.toLowerCase() === "gif"
                            || node.type.toLowerCase() === "bmp"
                        ){
                            $.cl.openFile(selectedNodeId);
                        }else{
                            $.cl.popupConfirm("不支持打开二进制文件。", null, false)
                        }
                    }
                },
                "rename": {
                    "label": "重命名",
                    "action": function () {
                        $.cl.showRenameDialog(selectedNodeId);
                    }
                },
                "rm": {
                    "label": "删除",
                    "action": function() {$.cl.showDeleteConfirmDialog(selectedNodeId)}
                },
                "share": {
                    "label": "分享",
                    "action": function(){$.cl.shareFile(selectedNodeId)}
                }
            }
        }
        let returnDat = {
            "new": {
                "label": "新建文档",
                "action": function () {
                    $.cl.showNewFileDialog(selectedNodeId);
                }
            },
            "mkdir": {
                "label": "新建文件夹",
                "action": function () {
                    $.cl.showMkdirDialog(selectedNodeId)
                }
            },
            "rm": {
                "label": "删除",
                "action": function () {
                    $.cl.showDeleteConfirmDialog(selectedNodeId)
                }
            },
            "rename": {
                "label": "重命名",
                "action": function () {
                    $.cl.showRenameDialog(selectedNodeId, true);
                }
            },
            "upload": {
                "label": "上传文件",
                "action": function () {
                    $("#file-input").data("path", selectedNodeId).trigger("click");
                }
            }
        };
        if (selectedNodeId === "/blog" || selectedNodeId === "blog") {
            returnDat["get_blog_ver"] = {
                "label": "查看详情",
                "action": function () {
                    $.cl.sendRequest({action: "get_blog_info"}, function (resp){
                        if (resp.code === 0) {
                            if (resp.last_update.length === 0) {
                                $.cl.popupMessage("尚未发布博客。")
                            } else {
                                let atCharIndex = window.contextData.loginInfo.email.indexOf("@");
                                let user = window.contextData.loginInfo.email.substring(0, atCharIndex),
                                    service = window.contextData.loginInfo.email.substring(atCharIndex + 1);
                                $.cl.popupMessage(
                                    "最后更新于: " + resp.last_update + "<br><br>" +
                                    '<a href="/notebook/publish/' +
                                    user + "/" + service + '/index.html" target="_blank">点击这里查看blog首页</a>'
                                )
                            }
                        } else {
                            $.cl.popupMessage(resp.msg);
                        }
                    })
                }
            }
            returnDat["refresh_blog"] = {
                "label": "发布",
                "action": function () {
                    $.cl.sendRequest({action: "refresh_blog"}, function (resp){
                        $.cl.popupMessage(resp.code === 0 ? "提交成功，开始发布！请稍后查看进度。" : resp.msg, "提示", 3);
                    });
                }
            }
        }
        return returnDat;
    },
    getAndRenderDefaultFileListAndPage: function(){
        var jstreeInstance = $("#jstree");
        if (jstreeInstance.jstree()){
            jstreeInstance.jstree().destroy()
        }
        jstreeInstance.jstree({
            core: {
                multiple: false,
                check_callback: true,
                data: [{
                    text: "游客的文件夹",
                    state: {opened: true},
                    children: [{
                        text: "README.md",
                        type: "md",
                        state: {opened: true, selected: true}
                    }]
                }]
            },
            types: $.cl.jstreeTypes,
            contextmenu: {
                select_node: false,
                items: {}
            },
            plugins: ["contextmenu", "types"]
        });
        document.getElementById('input-text-area').value = $("#default-file-content").val();
    },
    getAndRenderLoginedFileListAndPage: function(){
        var jstreeInstance = $("#jstree");
        if (jstreeInstance.jstree()){
            jstreeInstance.jstree().destroy()
        }
        jstreeInstance.on("ready.jstree", function(){
            let curDoc = $.cl.getCurrentDoc();
            if (curDoc.path !== undefined && curDoc.path.length > 0){
                $.cl.openFile(curDoc.path);
                $.cl.openJstreeNode(curDoc.path);
            }
        }).on("select_node.jstree", function (e, node) {
            if (["text", "md", "img"].indexOf(node.node.type) < 0) {
                return;
            }
            var selectedNodeId = node.node.id;
            if ($.cl.getCurrentDoc().path !== selectedNodeId) {
                $.cl.openFile(selectedNodeId);
            }
        }).on("open_node.jstree", function (e, node) {
            $.cl.onJstreeNodeOpen(e, node.node);
        }).jstree({
            core: {
                multiple: false,
                data: {
                    url: "/notebook/api",
                    type: "post",
                    dataType: "json",
                    contentType: "application/json",
                    data: function (node) {
                        return JSON.stringify({
                            path: node.id,
                            action: "listdir"
                        });
                    }
                }
            },
            types: $.cl.jstreeTypes,
            contextmenu: {
                select_node: false,
                items: $.cl.renderJstreeContextMenu
            },
            plugins: ["types", "contextmenu"]
        });
        document.getElementById('input-text-area').value = "";
    },
    renderLoginPage: function (){
        $.cl.releasePageResource();
        var navHtml = [
            '<span>欢迎回来，',
                '<a href="javascript:void(0)" id="change-passwd">',
                    '<i class="fa fa-group" aria-hidden="true"></i> ' + window.contextData.loginInfo.email,
                '</a>',
            '</span>',
            '<a href="javascript:void(0)" id="logout" ><i class="fa fa-sign-in" aria-hidden="true"></i> 注销</a>'
        ].join("");
        $(".right-nav").html(navHtml);
        $("#logout").off("click").click($.cl.logout);
        $("#change-passwd").off("click").click($.cl.showChangePasswordDialog);

        var leftNavHtml = [
            '<a href="javascript:void(0)" id="save-btn"><i class="fa fa-save" aria-hidden="true"></i> 保存</a>',
            '<a href="javascript:void(0)" id="history-btn"><i class="fa fa-history" aria-hidden="true"></i> 历史</a>'
        ].join("");
        $("#top-dynamic-nav").html(leftNavHtml);
        $("#save-btn").off("click").click($.cl.saveContent);
        $("#history-btn").off("click").click($.cl.selectHistory);
        $.cl.getAndRenderLoginedFileListAndPage();
        document.getElementById("jstree").addEventListener("drop", $.cl.onDropFileToJsTree, false);
        document.getElementById("input-text-area").addEventListener("drop", $.cl.onDropFileToJsTree, false);
    },
    releasePageResource: function (){},
    renderUnloginPage: function (){
        $.cl.releasePageResource();
        $("#input-text-area").prev().html("编辑");
        var navHtml = [
            '<a href="javascript:void(0)" id="login" ><i class="fa fa-sign-in" aria-hidden="true"></i> 登录</a>',
            '<a href="javascript:void(0)" id="register" ><i class="fa fa-table" aria-hidden="true"></i> 注册</a>'
        ].join("");
        $(".right-nav").html(navHtml);
        $("#login").off("click").click(function(){
            $("#login-or-regist").html("登录");
            $("#login-modal").modal("show");
        }).next().off("click").click(function(){
            $("#login-or-regist").html("注册");
            $("#login-modal").modal("show");
        });
        $("#login-btn").off("click").click(function(){
            $("#login-modal").modal("hide");
            return $("#login-or-regist").html() === "注册" ? $.cl.register() : $.cl.login();
        });
        $("#top-dynamic-nav").html("");
        $.cl.getAndRenderDefaultFileListAndPage();
    },
    saveContent: function (){
        if (!(window.contextData.loginInfo && window.contextData.loginInfo.email)){
            $.cl.popupMessage("请登录。");
            return ;
        }

        var nodeType = $("#jstree").jstree().get_node($.cl.getCurrentDoc().path).type;
        if (["md", "text"].indexOf(nodeType) < 0){
            return;
        }

        var content = $("#input-text-area").val();
        if (!content.trim(" \n\r\t")) return;

        let curDoc = $.cl.getCurrentDoc();
        if (curDoc.path === undefined || curDoc.length === 0) {
            return;
        }

        // 进入保存逻辑, range分两种情况
        // - all: 提交 content
        // - delta: 提交 base: int, dist_md5: str, diff: List
        let reqData = {action: "save", node_id: curDoc.path};
        if (curDoc.base === undefined) {
            // 没有 base，全量保存
            reqData["range"] = "all";
            reqData["content"] = content;
        } else {
            // 如果有版本号，则计算原始文档的diff
            reqData["range"] = "delta";
            reqData["base"] = curDoc.base;
            reqData["dist_md5"] = md5(content);

            let rawDiff = Diff.diffChars(curDoc.baseContent, content),
                postDiff = [];
            for (let i = 0; i < rawDiff.length; i++) {
                let d = rawDiff[i];
                if (d.added === undefined && d.removed === undefined) {
                    d.value = ""
                }
                postDiff.push(d)
            }
            reqData["diff"] = postDiff;
        }

        // 发送请求之前检查是否重复请求
        // 1. 禁止并发，检查是否在请求中
        // 2. 判断内容是否重复
        // 3. 绘制按钮
        if ($.cl.onSaveContent === true) {
            console.log("on saving")
            return;
        }
        if (reqData.range === "delta" && reqData.dist_md5 === $.cl.lastCommitMd5) {
            console.log("old content")
            $.cl.drawSaveSuccessAnimation();
            return;
        }
        $.cl.onSaveContent = true;
        $.cl.lastSavedContent = content;
        $.cl.lastSavedTime = Date.now();
        $.cl.drawSavingAnimation();

        $.cl.sendRequest(reqData, function (data) {
            // 保存成功后进入此
            $.cl.onSaveContent = false;

            // failed
            if (data.code !== 0){
                $.cl.popupMessage("操作失败。详细信息：" + data.msg);
                $.cl.drawSaveBtnInitState();
                return ;
            }

            // success
            $.cl.drawSaveSuccessAnimation();
            if (reqData.range === "delta") {
                $.cl.lastCommitMd5 = reqData.dist_md5;
            }

            let curDoc = $.cl.getCurrentDoc();
            if (data.base === curDoc.base) {
                $.cl.setCurrentDoc({version: data.version})
            } else {
                $.cl.setCurrentDoc({version: data.version, base: data.base, baseContent: content})
            }
        }, function (resp) {
            // 保存失败进入此
            $.cl.onSaveContent = false;
            $.cl.drawSaveBtnInitState();
            $.cl.popupMessage(resp.msg || "保存失败");
        });
    },
    showHistoryBusy: false,
    showHistoryDiff: function () {
        if ($.cl.showHistoryBusy === true) {
            console.log("showHistoryBusy busy");
            return;
        }
        $.cl.showHistoryBusy = true;

        $(".history-item").removeClass("history-item-selected");
        $(this).addClass("history-item-selected");

        let curDoc = $.cl.getCurrentDoc(),
            version = $(this).data("version"),
            createTime = $(this).data("create_time");
        $.cl.sendRequest({action: "diff", "node_id": curDoc.path, version: version}, function (resp) {
            $.cl.showHistoryBusy = false;

            let diffChars = Diff.diffChars(resp.last_content, resp.current_content),
                renderHtml = [
                    '<div class="history-revert clickable">' +
                    '<i class="fa fa-undo" aria-hidden="true"></i> 恢复 ' + '[' + createTime + '] 版本: ' + version +
                    '</div>'
                ];
            for (let i = 0; i < diffChars.length; i++){
                let d = diffChars[i];
                let encodedStr = document.createElement('div').appendChild(document.createTextNode(d.value)).parentNode.innerHTML;

                if (d.removed === true) {
                    renderHtml.push('<span style="text-decoration: line-through;background-color: #ffd0d4">' + encodedStr + '</span>');
                } else if (d.added === true) {
                    renderHtml.push('<span style="color: #3c744a; background-color: #b6ecbf">' + encodedStr + '</span>');
                } else {
                    renderHtml.push(encodedStr)
                }
            }
            $(".history-view-body").html(renderHtml.join(""));
            $(".history-revert").off("click").click(function (){
                document.getElementById('input-text-area').value = resp.current_content;
                $("#close-history-window").trigger("click");

                // clear old context
                $(".history-view-body").html("请在左侧选择一个版本查看差异。")
            });
        }, function () {
            $.cl.showHistoryBusy = false;
        });
    },
    selectHistory: function () {
        let curDoc = $.cl.getCurrentDoc();
        if (curDoc.path === undefined || curDoc.path.length === 0) {
            $.cl.popupMessage("请打开一个文本文件来查看历史");
            return;
        }

        let historyWindow = $(".history-window");
        $("#close-history-window").off("click").click(function (){historyWindow.fadeOut(250)});
        historyWindow.fadeIn(250);
        // 发送请求，获取历史记录
        $(".history-view-body").html("");
        $.cl.sendRequest({action: "history", "node_id": curDoc.path}, function (resp) {
            // 渲染dom
            if (resp.code !== 0) {
                $.cl.popupMessage(resp.msg);
                return;
            }
            if (resp.history.length === 0){
                $(".history-list").html("已为最新版本，无历史");
                return;
            }
            let historyHtml = [];
            for (let i = 0; i < resp.history.length; i++) {
                let h = resp.history[i];
                historyHtml.push(
                    '<li class="clickable history-item" data-version="' + h.version + '" ' +
                    'data-create_time="' + h.create_time + '">[' + h.create_time + '] 版本' + h.version + ', ' + h.lines + '处差异</li>')
            }
            $(".history-list").html('<ul>' + historyHtml.join('') + '</ul>');
            $(".history-item").off("click").click($.cl.showHistoryDiff);
        })
    },
    daemonToTransMdId: undefined,
    oldContent: undefined,
    lastSavedTime: 0,
    lastSavedContent: undefined,
    daemonToTransMd: function (){
        // 定时将mark down转换为html
        return setInterval(function(){
            var newContent = $("#input-text-area").val();
            if (newContent !== $.cl.oldContent){
                $.cl.oldContent = newContent;
                $("#content-text").html(marked(newContent));
                hljs.highlightAll();
            }
            let current = Date.now();
            if ($.cl.lastSavedContent === undefined) {
                $.cl.lastSavedContent = newContent;
            }
            if ($.cl.lastSavedContent !== newContent && (current - $.cl.lastSavedTime) >= (1000 * 5)) {
                $("#save-btn").trigger("click");
            }
        }, 400);
    },
    insertStrToTextarea: function(str){
        var obj = document.getElementById("input-text-area");
        if (document.selection) {
            var sel = document.selection.createRange();
            sel.text = str;
        }else if(typeof obj.selectionStart === "number" && typeof obj.selectionEnd === "number") {
            var startPos = obj.selectionStart,
                endPos = obj.selectionEnd,
                cursorPos = startPos,
            tmpStr = obj.value;
            obj.value = tmpStr.substring(0, startPos) + str + tmpStr.substring(endPos, tmpStr.length);
            cursorPos += str.length;
            obj.selectionStart = obj.selectionEnd = cursorPos;
        }
    },
    uploadFile: function (file, path){
        var data = new FormData();
        data.set("file", file);
        data.set("node_id", path);
        data.set("action", "upload_file");

        $.ajax({
            url: "/notebook/upload",
            type: "post",
            data: data,
            cache: false,
            processData: false,
            contentType: false,
            success: function(data){
                if (data.code === 0){
                    $.cl.popupMessage("上传成功！", null, 3);
                    $("#jstree").jstree().refresh_node(path);
                    let thisDoc = path === "/" ? ("/" + file.name) : (path + "/" + file.name),
                        curDoc = $.cl.getCurrentDoc();

                    if (thisDoc === curDoc.path){
                        $.cl.openFile(thisDoc);
                    }
                }else{
                    $.cl.popupConfirm(data.msg, null, false, "上传失败");
                }
            },
            error: function(e){
                $.cl.popupMessage("操作失败！请检查你的网络。")
            }
        });
    },
    onDropFileToJsTree: function (e){
        e.preventDefault();
        var fileList = e.dataTransfer.files;
        if(fileList.length === 0){
            return false;
        }
        var file = fileList[0];
        if (!file.name.match(/^[\.a-zA-Z0-9_\u4e00-\u9fa5]+$/)){
            $.cl.popupConfirm("文件名仅允许包含数字、字母、下划线以及汉字，不支持其它字符。请返回修改。", null, false, "文件名有误");
            return false;
        }

        var filesize = Math.floor((fileList[0].size)/1024);
        if(filesize > 1024*200){
            $.cl.popupConfirm("上传的文件大小不能超过200MB。", null, false, "文件大小超过限制");
            return false;
        }

        var path = $("#jstree").jstree().get_top_selected(true);
        if (path.length < 1){
            path = "/";
        }else{
            path = (path[0].type === "folder" ? path[0].id : path[0].parent);
            if (path[path.length - 1] !== "/"){
                path += "/";
            }
        }        var promptMsg = [
            "<p>将“" + file.name + "”保存到“"+ path +"”?</p>",
            '<p>这个路径可能是系统默认的，但如果你想改变存放的地方，请在左侧的目录结构中点击你想保存的位置，然后再按下“Ctrl”和“S”键。</p>'
        ].join("");
        $.cl.popupConfirm(
            promptMsg,
            function(){$.cl.uploadFile(file, path)},
            null,
            "上传文件"
        );
    },
    compatibilityChecking: function (){
        if(localStorage.clearCompatibilityPrompt !== "c"){
            var compatible = false;
            var naString = navigator.userAgent || "";

            var isChrome = naString.toLowerCase().indexOf("chrome");
            compatible |= (isChrome > -1 && parseInt(naString.substr(isChrome + 7 /* the length of "chrome/" */)) > 50);

            var isSafari = naString.toLowerCase().indexOf("safari");
            compatible |= (isSafari > -1 && parseInt(naString.substr(isSafari + 7 /* the length of "safari/" */)) > 536);

            if (!compatible){
                $("#browser-prompt").css({display: "block"}).find("a").off("click").click(function(){
                    $("#browser-prompt").css({display: "none"});
                    localStorage.clearCompatibilityPrompt = "c";
                });
            }
        }
    },
    initPage: function (){
        $.cl.compatibilityChecking();
        $.cl.initPageSplitWidth();
        (window.contextData.loginInfo && window.contextData.loginInfo.email ? $.cl.renderLoginPage : $.cl.renderUnloginPage)();
        $("input[name=password]").on('keyup', function(e){if(e.key === "Enter"){$("#login-btn").trigger("click")}});
        if ($.cl.daemonToTransMdId){
            clearInterval($.cl.daemonToTransMdId);
        }
        $("#file-input").change(function(){
            var file = $(this)[0].files[0],
                path = $(this).data("path");
            $.cl.uploadFile(file, path);
        });
        $.cl.daemonToTransMdId = $.cl.daemonToTransMd();
        if (window.markedImageParseCB === undefined) {
            window.markedImageParseCB = (href) => {
                let availPrefix = [
                    "http://",
                    "https://",
                    "/notebook/img_preview/",
                    "/notebook/share/",
                    "/notebook/static/",
                ]
                for (let i = 0; i < availPrefix.length; i++){
                    if (href.indexOf(availPrefix[i]) === 0) {
                        return href
                    }
                }
                let username = window.contextData.loginInfo.email.split("@", 1);
                let service = window.contextData.loginInfo.email.substring(username.length + 1);
                if (href[0] === "/") {
                    return "/notebook/img_preview/" + username + "/" + service + href;
                } else {
                    let curDoc = $.cl.getCurrentDoc();
                    let index = curDoc.path.lastIndexOf("/");
                    let parentPath = curDoc.path.slice(0, index);
                    return "/notebook/img_preview/" + username + "/" + service + "/" + parentPath + "/" + href;
                }
            }
        }
        /*
         * drag event
         * ctrl key event
         * tab key event
         */
        $(document).on({
            dragleave: $.cl.preventDefault,
            drop: $.cl.preventDefault,
            dragenter: $.cl.preventDefault,
            dragover: $.cl.preventDefault,
            keydown: function(event){
                if(event.keyCode === 9){
                    if($("#input-text-area").is(":focus")){
                        // 在编写代码时插入 \t
                        event.preventDefault();

                        let thisDoc = $.cl.getCurrentDoc().path,
                            insertChar = "    ";
                        if (thisDoc.length > 0 && thisDoc.substring(thisDoc.length - 2).toLowerCase() === "py") {
                            insertChar = "\t";
                        }
                        $.cl.insertStrToTextarea(insertChar);
                    }
                    return ;
                }
                if(event.ctrlKey  &&  event.keyCode === 83){
                    event.preventDefault();
                    $("#save-btn").trigger("click");
                }
            }
        })
    },
};

$(window).resize($.cl.windowSizeMonitor).on("ready", $.cl.windowSizeMonitor);
$($.cl.initPage);
