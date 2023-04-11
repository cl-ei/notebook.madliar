$.cl = {
    jstreeTypes: {
        bin: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/bin.png"},
        img: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/img.png"},
        text: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/file.png"},
        md: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/file.png"},
        folder: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/folder.png"},
        default: {icon: (window.CDN_URL || "") + "/notebook/static/img/jstree/folder.png"}
    },
    windowSizeMonitor: function (){
        if(document.documentElement.clientWidth < 605){
            $("#browser-prompt, #nav, #content").css({"display": "none"});
            $("#uavaliable-mask").css({"display": "block"});
        }else{
            $("#nav, #content").css({"display": "block"});
            $("#browser-prompt, #uavaliable-mask").css({"display": "none"});
            $.cl.compatibilityChecking();
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
    onSaveContent: false,
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

    docContent: "",
    getCurrentDoc: function () {
        return {
            path: localStorage.docPath === undefined ? "" : localStorage.docPath,
            version: localStorage.docVer === undefined ? "" : localStorage.docVer,
            content: $.cl.docContent,
        }
    },
    setCurrentDoc: function (option) {
        // 如果设置其他两项，则 path 保持
        // 如果设置 path 而未指定 ver 和 content, 则清空后两者
        if (option.path !== undefined) {
            localStorage.docPath = option.path;
        }
        localStorage.docVer = option.version || "";
        $.cl.docContent = option.content || "";
    },

    openJstreeNode: function (nodeId){
        let layers = [];
        if(nodeId !== "/"){
            layers = nodeId.substring(1, nodeId.length).split("/");
        }
        let jst = $("#jstree").jstree();

        function recursionOpenJstreeNode(layer){
            if (layer > layers.length){
                return;
            }

            let thisNode = "/";
            if (layer > 0){
                let lys = [];
                for (let i = 0; i < layer; i++){
                    lys.push(layers[i]);
                }
                thisNode = "/" + lys.join("/");
            }

            let node = jst.get_node(thisNode);
            if (node === false) {
                return
            }
            if (node.state.opened === true){
                // 本节点已经展开，直接进入下一层
                recursionOpenJstreeNode(layer + 1);
            } else {
                // 展开本节点，并进入下一层
                $("#jstree").on("open_node.jstree", function(){
                    recursionOpenJstreeNode(layer + 1);
                }).jstree().open_node(thisNode);
            }
        }
        recursionOpenJstreeNode(0);
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
                    $("#jstree").jstree().refresh_node(nodeId);
                    $.cl.openJstreeNode(nodeId + "/" + dirName);
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
            var onRenameResponsed = function (data){
                if(data.code === 0){
                    $.cl.popupMessage("重命名成功！", null, 3);
                    var nodePath = nodeId.split("/").slice(0, -1).join("/") || "/";
                    $("#jstree").jstree().refresh_node(nodePath);
                    if (nodeId === $.cl.getCurrentDoc().path){
                        $.cl.setCurrentDoc({path: nodePath + "/" + dirName})
                        $.cl.renderCurrentEditDocumentTitle();
                    }
                }else{
                    $.cl.popupMessage("重命名失败：" + data.msg);
                }
            };
            $.cl.sendRequest({action: "rename", node_id: nodeId, new_name: dirName}, onRenameResponsed);
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
            var onNewFileResponsed = function (data){
                if(data.code === 0){
                    let jst = $("#jstree").jstree();
                    $.cl.popupMessage("创建成功！", null, 3);
                    jst.refresh_node(nodeId);
                    $.cl.openJstreeNode(nodeId + "/" + fileName);
                }else{
                    $.cl.popupMessage("创建失败：" + data.msg);
                }
            };
            $.cl.sendRequest({action: "new", node_id: nodeId, file_name: fileName}, onNewFileResponsed);
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
        var onFileOpenedResponsed = function (data){
            $.cl.onOpenFile = false;
            if (data.code !== 0){
                var msg = "操作失败。详细信息：" + data.msg;
                $.cl.popupMessage(msg);
                return ;
            }

            $.cl.setCurrentDoc({path: data.path, version: data.version, content: data.content});
            $.cl.renderCurrentEditDocumentTitle();

            if (data.img !== true){
                document.getElementById('input-text-area').value = data.content;
                return;
            }

            // 预览图片，渲染dom
            var new_url = window.location.protocol + "//" + window.location.host + "/notebook/" + data.key;
            document.getElementById('input-text-area').value = [
                "<img src=\"",
                new_url,
                "\" style=\"width:100%\">"
            ].join("");
        };
        var onOpenFileFailed = function (e){
            $.cl.onOpenFile = false;
            $.cl.popupMessage("操作失败，请检查你的网络连接。")
        };
        $.cl.sendRequest({action: "open", "node_id": nodeId}, onFileOpenedResponsed, onOpenFileFailed);
    },
    shareFile: function(nodeId){
        var onShareResponsed = function (data){
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
        };
        $.cl.sendRequest({action: "share", node_id: nodeId}, onShareResponsed)
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
        return {
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
                        text: "简介",
                        type: "text",
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
            if (curDoc.path.length > 0){
                $.cl.openJstreeNode(curDoc.path);
                $.cl.openFile(curDoc.path);
            }
        }).on("select_node.jstree", function (e, node){
            if (["text", "md", "img"].indexOf(node.node.type) < 0) return;
            var selectedNodeId = node.node.id;
            if ($.cl.getCurrentDoc().path !== selectedNodeId){
                $.cl.openFile(selectedNodeId);
            }
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
            '<a href="javascript:void(0)" id="save-btn"><i class="fa fa-save" aria-hidden="true"></i> 保存</a>'
        ].join("");
        $("#top-dynamic-nav").html(leftNavHtml);
        $("#save-btn").off("click").click($.cl.saveContent);
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

        // 进入保存逻辑
        let curDoc = $.cl.getCurrentDoc();

        if (curDoc.path.length > 0){
            let reqData = {action: "save", node_id: curDoc.path};
            if (curDoc.version.length > 0 && curDoc.content.length > 0) {
                // 如果有版本号，则计算原始文档的diff
                reqData["range"] = "delta";
                reqData["based_version"] = curDoc.version;

                let rawDiff = Diff.diffChars(curDoc.content, content),
                    postDiff = [];
                for (let i = 0; i < rawDiff.length; i++) {
                    let d = rawDiff[i];
                    if (d.added === undefined && d.removed === undefined) {
                        d.value = ""
                    }
                    postDiff.push(d)
                }
                reqData["diff"] = postDiff
                reqData["base_md5"] = md5(curDoc.content);
            } else {
                // 没有版本号，全量保存
                reqData["range"] = "all";
                reqData["content"] = content;
            }

            $.cl.clearMessage();
            $.cl.sendRequest(reqData, function (data) {
                // 保存成功后进入此
                // TODO：也许需要重新处理 version
                if (data.code !== 0){
                    $.cl.popupMessage("操作失败。详细信息：" + data.msg);
                    return ;
                }
                $.cl.popupMessage("保存成功！", null, 2)
                $.cl.setCurrentDoc({version: data.version, content: content})
            });
            return ;
        }
        /* show confirm
        console.log("confirm?")
        var path = "",
            topSelected = $("#jstree").jstree().get_top_selected(true);
        if (topSelected.length < 1){
            path = window.contextData.loginInfo.email;
        }else{
            path = topSelected[0].type === "folder" ? topSelected[0].id : topSelected[0].parent;
        }
        $.cl.showSaveContentDialog(path, content);
        */
    },
    daemonToTransMdId: undefined,
    oldContent: undefined,
    daemonToTransMd: function (){
        // 定时将mark down转换为html
        return setInterval(function(){
            var newContent = $("#input-text-area").val();
            if (newContent !== $.cl.oldContent){
                $.cl.oldContent = newContent;
                $("#content-text").html(marked(newContent));
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
        (window.contextData.loginInfo && window.contextData.loginInfo.email ? $.cl.renderLoginPage : $.cl.renderUnloginPage)();
        $("input[name=password]").on('keyup', function(e){if(e.key === "Enter"){$("#login-btn").trigger("click")}});
        if ($.cl.daemonToTransMdId){
            clearInterval($.cl.daemonToTransMdId);
        }
        $("#jstree-outdent").off("click").click(function(){
            $("#folder-tree").fadeOut(0);
            $("#show-folder-tree").fadeIn(0);
            $("#sub-content").addClass("sub-content-full-screen");
        });
        $("#show-folder-tree").off("click").click(function(){
            $("#folder-tree").fadeIn(0);
            $("#show-folder-tree").fadeOut(0);
            $("#sub-content").removeClass("sub-content-full-screen");
        });
        $("#file-input").change(function(){
            var file = $(this)[0].files[0],
                path = $(this).data("path");
            $.cl.uploadFile(file, path);
        });
        $.cl.daemonToTransMdId = $.cl.daemonToTransMd();
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
    preventDefault: function (e){e.preventDefault()}
};

$(window).resize($.cl.windowSizeMonitor).on("ready", $.cl.windowSizeMonitor);
$($.cl.initPage);
