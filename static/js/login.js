function rsa_encryption(password, public_key) {
    var encrypt = new JSEncrypt();
    encrypt.setPublicKey(public_key);
    return encrypt.encrypt(password);
}

$("#password").keypress(function(e) {
    if (e.which === 13) {
        // // console.log("press enter");
        $("#login-btn").click();
    }
});

$("#show-btn").click(function() {
    if ($("#password").attr("type") === "password") {
        $("#password").attr("type", "text");
        $("#show-btn").addClass("show");
    } else {
        $("#password").attr("type", "password");
        $("#show-btn").removeClass("show");
    }
});

$("#login-btn").click(function() {
    // console.log("click btn")
    $.get("/api/login", function(data) {
        // console.log(data);
        if (data.errno === 0) {
            // console.log("keyno:" + data.data.keyno);
            // console.log("public_key:" + data.data.key);
            var password = $("#password").val();
            // console.log("password:" + password);
            password = rsa_encryption(password, data.data.key);
            // console.log("password:" + password);
            var obj = {
                "keyno": data.data.keyno,
                "password": password
            }
            $.ajax({
                url: "/api/login",
                type: "post",
                contentType: "application/json",
                data: JSON.stringify(obj),
                success: function(data) {
                    if (data.errno === 0) {
                        // 登录成功跳转到主页
                        alert("登录成功");
                        $(window).attr("location", "/");
                    } else {
                        alert("登录失败");
                        $("#password").val("");
                        $("#password").focus();
                    }
                }
            });
        } else {
            alert("登录失败");
            $("#password").val("");
            $("#password").focus();
        }
    });
});

$(function() {
    $.get("/api/verification", function(data) {
        //检测是否已经登录
        if (data.errno === 0) {
            $(window).attr("location", "/");
        }
    });
});