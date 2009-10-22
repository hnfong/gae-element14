var util = {}

util.hash2request = function (post_content) {
    var post_array = new Array();
    for (var i in post_content) {
        var v = post_content[i];
        switch(typeof v) {
            case 'string':
            case 'number':
                post_array.push( '' + encodeURIComponent(i) + '=' + encodeURIComponent(v) );
                break;
            case 'object':
                if (v instanceof Array) {
                    for (var j = 0 ; j < v.length; j++)  {
                        post_array.push('' + encodeURIComponent(i) + '=' + encodeURIComponent(v[j]));
                    }
                }
                break;
        }
    }

    return post_array.join('&');
};

util.ajax_async = function (url, post_content, func)
{
    var post_string;
    if (typeof post_content == 'string') {
        post_string = post_content;
    } else {
        post_string = util.hash2request(post_content);
    }
    var http = newHTTP();
    if (!http) return false;

    http.open("POST", url, true);
    http.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    http.onreadystatechange = function () {
        if (http.readyState == 4) {
            try {
                http.status;
                http.responseText;
            } catch (e) {
                return false;
            }
            func(http);
        }
    };

    http.send(post_string);
};


function newHTTP(){
    var xmlhttp=false;
    /*@cc_on @*/
    /*@if (@_jscript_version >= 5)
    // JScript gives us Conditional compilation, we can cope with old IE versions.
    // and security blocked creation of the objects.
     try {
      xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
     } catch (e) {
      try {
       xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
      } catch (E) {
       xmlhttp = false;
      }
     }
    @end @*/
    if (!xmlhttp && typeof XMLHttpRequest!='undefined') {
        try {
            xmlhttp = new XMLHttpRequest();
        } catch (e) {
            xmlhttp=false;
        }
    }
    if (!xmlhttp && window.createRequest) {
        try {
            xmlhttp = window.createRequest();
        } catch (e) {
            xmlhttp=false;
        }
    }
    return xmlhttp;
}
