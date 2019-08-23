$(document).ready(function() {
    namespace = '/graphSock';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);



    socket.on('connect', function() {
                console.log('I\'m connected!');
            });

    socket.on('restart', function(msg) {
        for (i = 0; i < msg.tickers; i++) {
            console.log('restarting ti_content-' + i)
            var elm = document.getElementById("ti_content-" + i);
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
        var elm = document.getElementById("ti_content-" + msg.ticker);
        var newone = elm.cloneNode(true);
        newone.innerHTML = msg.html;
        elm.parentNode.replaceChild(newone, elm);
        var width = newone.offsetWidth;
        var new_speed = width / 64;
        console.log(new_speed + 's')
        console.log(width)
        newone.style.animationDuration = new_speed + 's';
    });

    socket.on('update-vr', function(msg) {
        console.log(msg)
        var tweet = document.getElementById("tweet");
        var sentiment = document.getElementById("sentiment");
        var joy = document.getElementById("joy");
        var anger = document.getElementById("anger");
        var disgust = document.getElementById("disgust");
        var sadness = document.getElementById("sadness");
        var fear = document.getElementById("fear");
        tweet.innerHTML = msg.tweet;
        sentiment.innerHTML = msg.sentiment;
        joy.innerHTML = msg.joy;
        anger.innerHTML = msg.anger;
        disgust.innerHTML = msg.disgust;
        sadness.innerHTML = msg.sadness;
        fear.innerHTML = msg.fear;
    });

    socket.on('update-bar', function(msg) {
        barchart.updateSeries([{data:[
            msg.joy, msg.anger, msg.disgust, msg.sadness, msg.fear
        ]}])
    });

    socket.on('update-tweets', function(msg) {
        console.log('Updating Tweets')
        var parent = document.getElementById('tweets');
        parent.insertBefore(parent.firstChild, parent.lastChild);
    });

    socket.on('update-heatmap', function(msg) {
        console.log(msg)
        console.log('Updating heatmap')
        addPoint(msg.lat, msg.lng);
    });
 });