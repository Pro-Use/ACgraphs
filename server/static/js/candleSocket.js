$(document).ready(function() {
    namespace = '/graphSock';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);



    socket.on('connect', function() {
                console.log('I\'m connected!');
            });

    socket.on('update-candle', function(msg) {
        candlechart.updateSeries([{data:[
            msg.data
        ]}])
    });

    var screen_num = 2;

    socket.on('update-bg', function(msg) {
        console.log(msg)
        if (msg.screens.includes(screen_num)) {
            $("body").css("background-size", "cover");
            $("body").css("background-image", "url('static/images/screen"+screen_num+"_"+msg.bg+".jpg')");
        }
    });
 });