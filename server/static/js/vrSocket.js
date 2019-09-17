$(document).ready(function() {
    namespace = '/graphSock';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);


    socket.on('update-vr-tweet', function(msg) {
        console.log(msg)
        var tweet = document.getElementById("tweet");
        var t_sentiment = document.getElementById("t-sentiment");
        var joy = document.getElementById("joy");
        var anger = document.getElementById("anger");
        var disgust = document.getElementById("disgust");
        var sadness = document.getElementById("sadness");
        var fear = document.getElementById("fear");
        tweet.innerHTML = msg.tweet;
        t_sentiment.innerHTML = msg.sentiment;
        joy.innerHTML = msg.joy;
        anger.innerHTML = msg.anger;
        disgust.innerHTML = msg.disgust;
        sadness.innerHTML = msg.sadness;
        fear.innerHTML = msg.fear;
    });

        socket.on('update-vr-news', function(msg) {
        console.log(msg)
        var news = document.getElementById("news");
        var n_sentiment = document.getElementById("n-sentiment");
        news.innerHTML = msg.news;
        n_sentiment.innerHTML = msg.sentiment;
    });


 });