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
    var current_bg = null

    socket.on('update-bg', function(msg) {
        console.log(msg)
        if (msg.screens.includes(screen_num)) {
            $("#bg_"+msg.bg).show();
            if (current_bg != null) {
                $("#bg_"+current_bg).hide();
            }
            if ( [99,].includes(parseInt(msg.bg)) ){
                $('li.news-list-item.row-max.green').css('color', '#fff;')
            } else {
                $('li.news-list-item.row-max.green').css('color', '#9ed600;')
            }
            current_bg = msg.bg;
        }
    });

    for (i = 0; i < 11; i++) {
        $('body').append('<div id=bg_'+i+' class=page-bg></div>');
        $("#bg_"+i).css("background-image", "url('static/images/b"+i+"_"+screen_num+".jpg')")
    }

    socket.on('change', function(msg){
      var parent = document.getElementById('news');
      parent.insertBefore(parent.firstElementChild, parent.lastElementChild);
    });

//    update_news();

    $('body').css('cursor', 'none');
 });