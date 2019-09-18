$(document).ready(function() {
    namespace = '/graphSock';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);



    socket.on('connect', function() {
                console.log('I\'m connected!');
            });

    socket.on('restart', function(msg) {
        for (i = 0; i < msg.tickers; i++) {
            console.log('restarting ti_content')
            var elm = document.getElementById("ti_content");
            var newone = elm.cloneNode(true);
            elm.parentNode.replaceChild(newone, elm);
            var width = newone.offsetWidth;
            var new_speed = width / 64;
            console.log(new_speed + 's')
            console.log(width)
            newone.style.animationDuration = new_speed + 's';
        }
    });

    socket.on('update', function(msg) {
        console.log("new news")
        var elm = document.getElementById("ti_content");
        var newone = elm.cloneNode(true);
        newone.innerHTML = msg.html;
        elm.parentNode.replaceChild(newone, elm);
        var width = newone.offsetWidth;
        var new_speed = width / 64;
        console.log(new_speed + 's')
        console.log(width)
        newone.style.animationDuration = new_speed + 's';
    });

    socket.on('update-tweets', function(msg) {
        console.log('Updating tweets')
        $("#left-news-feed").append(msg.html);
    });

    var screen_num = $("body").data('screen');

    socket.on('update-bg', function(msg) {
        console.log(msg)
        if (msg.screens.includes(screen_num)) {
            $("body").css("background-size", "cover");
            $("body").css("background-image", "url('static/images/screen"+screen_num+"_"+msg.bg+".jpg')");
        }
    });


    socket.on('change', function(msg){
      var parent = document.getElementById('left-news-feed');
      parent.insertBefore(parent.firstElementChild, parent.lastElementChild);
    });


 });