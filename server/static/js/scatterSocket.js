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
                max: parseFloat(msg.min_max[1]),
                labels: {
                    show: true,
                    align: 'left',
                    style: {
                      color: 'rgb(158,214,0)',
                      fontSize: '19px',
                      fontFamily: 'doublet',
                      cssClass: 'scatter-yaxis-label',
                    },
                    formatter: function(val, index) {
                        return Math.round(val) + '%';
                    },
                },
              }
            })

        scatterchart.updateSeries([{name: "happy",
        data: msg.happy
        }, { name: "sad",
        data: msg.sad
        } ])
    });

    var screen_num = 5;
    var current_bg = null

    socket.on('update-bg', function(msg) {
        console.log(msg)
        if (msg.screens.includes(screen_num)) {
            $("#bg_"+msg.bg).show();
            if (current_bg != null) {
                $("#bg_"+current_bg).hide();
            }
            current_bg = msg.bg;
        }
    });

    for (i = 0; i < 11; i++) {
        $('body').append('<div id=bg_'+i+' class=page-bg></div>');
        $("#bg_"+i).css("background-image", "url('static/images/B"+i+"_"+screen_num+".jpg')")
    }

    $('body').css('cursor', 'none');
 });