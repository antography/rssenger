
document.getElementById("gosendmsg").addEventListener("click", sendmsg)
document.getElementById("clear").addEventListener("click", clear)

document.getElementById("login").addEventListener("click", login)
document.getElementById("logout").addEventListener("click", logout)

var errorbox = document.getElementById("infozone")
var messgbox = document.getElementById("msgzone")
var inroom = false
var myroom = ""
var myuser = ""

var socket = io();

socket.on('message', data => {
    errorbox.value = data + "\n" + errorbox.value;
});
socket.on('close', function()
{
    inroom = false
    document.getElementById("myroom").innerHTML = "No Feed"
    document.getElementById("myuser").innerHTML = "No User"
    document.title = "No Feed"
    errorbox.value = "Socket closed" + "\n" + errorbox.value;
    myroom = ""
    myuser = ""
});
socket.on('error', function()
{
    inroom = false
    document.getElementById("myroom").innerHTML = "No Feed"
    document.getElementById("myuser").innerHTML = "No User"
    document.title = "No Feed"
    errorbox.value = "Socket error" + "\n" + errorbox.value;
    myroom = ""
    myuser = ""
});

socket.on('getnewmsg', data => {
    fetch("/" + "getmsg"+ "/" +myroom+ "/" + data).then(res => res.json()).then(d => { 
        console.log(d) 
        var obj = d
        messgbox.value =  "[" + obj.msguser + "@rssenger " + myroom + "]$ " + obj.msgcont + "\n"+ messgbox.value 
    }) 
});

socket.on('setRoom', data => {
    document.getElementById("myroom").innerHTML = data
    myroom = data
    inroom = true
    document.title = data
    errorbox.value = "Connected to feed " + data + "\n" + errorbox.value;

});
socket.on('setUser', data => {
    document.getElementById("myuser").innerHTML = data
    myuser = data
    errorbox.value = "Connected to user " + data + "\n" + errorbox.value;

});

socket.on('remRoom', data => {
    inroom = false
    document.getElementById("myroom").innerHTML = "No Feed"
    document.getElementById("myuser").innerHTML = "No User"
    document.title = "No Feed"
    errorbox.value = "Left feed " + myroom + "\n" + errorbox.value;
    errorbox.value = "Left user " + myuser + "\n" + errorbox.value;
    myroom = ""
    myuser = ""

});

function login(){
    if (inroom == true){
        errorbox.value =  "ALREADY IN A FEED\n" + errorbox.value;
    } else {
        errorbox.value = "Attempting to connect" + "\n" + errorbox.value
        var info = revaluserroom()
        if (info[1] == ""){
            errorbox.value = "EMPTY FEED" + "\n" + errorbox.value
        }else if (info[0] == ""){
            errorbox.value = "EMPTY USERNAME" + "\n" + errorbox.value
        }
        else {
            socket.emit("join", {"username":info[0], "room":info[1]})
        }
        messgbox.value = ""
    }
}

function logout(){
    if (inroom == false){
        errorbox.value =  "NOT IN A FEED\n" + errorbox.value;
    } else {
        socket.emit("leave", {"username":myuser, "room":myroom})
        messgbox.value = ""
    } 
}

function sendmsg() {
    if (inroom == true) {
        var usrmsg = revalmsg()
        socket.emit('message', usrmsg)
        errorbox.value = "Sent msg: " + usrmsg + "\n" + errorbox.value
    } else {
        errorbox.value =  "NOT IN A FEED" + "\n" + errorbox.value
    }
    
}
function clear(){
    errorbox.value = ""
}

function revalmsg(){
    return document.getElementById("dermessage").value;
}

function revaluserroom(){
    var username = document.getElementById("username").value;
    var mkjroom = document.getElementById("mkjroom").value;
    var reval = [ username, mkjroom]
    return reval
}

var getJSON = function(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'json';
    xhr.onload = function() {
      var status = xhr.status;
      if (status === 200) {
        callback(null, xhr.response);
      } else {
        callback(status, xhr.response);
      }
    };
    xhr.send();
};
