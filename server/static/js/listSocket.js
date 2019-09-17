$(document).ready(function() {
    namespace = '/graphSock';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);



    socket.on('connect', function() {
                console.log('I\'m connected!');
            });

   socket.on('update-news-list', function(msg) {
        console.log('Updating News List')
        $('.list-container').empty();
        for (i = 0; i < msg.html_arr.length; i++) {
            $('.list-container').append(msg.html_arr[i]);
        }
    });

    var screen_num = $("body").data('screen');

    socket.on('update-bg', function(msg) {
        console.log(msg)
        if (msg.screens.includes(screen_num)) {
            $("body").css("background-size", "cover");
            $("body").css("background-image", "url('static/images/screen"+screen_num+"_"+msg.bg+".jpg')");
            if (msg.bg == 1) {
                $("list-container").css("color", "lime");
            } else {
                $("list-container").css("color", "white");
            }
        }
    });

    socket.on('change', function(msg){
      var parent = document.getElementById('news');
      parent.insertBefore(parent.firstElementChild, parent.lastElementChild);
    });

    update_news();
 });