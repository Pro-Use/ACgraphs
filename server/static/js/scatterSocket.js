$(document).ready(function() {
    namespace = '/graphSock';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);



    socket.on('connect', function() {
                console.log('I\'m connected!');
            });

    socket.on('update-scatter', function(msg) {
        console.log(msg)
        scatterchart.updateOptions({
              yaxis: {
                min: parseFloat(msg.min_max[0]),
                max: parseFloat(msg.min_max[1])
              }
            })

        scatterchart.updateSeries([{name: "happy",
        data: msg.happy
        }, { name: "sad",
        data: msg.sad
        } ])
    });

    var screen_num = 5;

    socket.on('update-bg', function(msg) {
        console.log(msg)
        if (msg.screens.includes(screen_num)) {
            $("body").css("background-size", "cover");
            $("body").css("background-image", "url('static/images/screen"+screen_num+"_"+msg.bg+".jpg')");
        }
    });
 });