function debug(s) {
 var d = document.createElement('DIV')
 d.appendChild( document.createTextNode( s ) )
 document.body.appendChild( d ) ;
}
window.onload = function() {
 for (var i = 0; i < document.forms.length; i ++) {
  var frm = document.forms[i];

  for (var j = 0 ; j < frm.elements.length; j++ ){
   var inp = frm.elements[j];
   if (inp.type == 'submit') {
    inp.onclick = function() { this.form.submitter = this; }
   }
  }

  frm.onsubmit = function(e) {
   var d = new Object();
   for (var j = 0 ; j < this.elements.length; j ++ ) {
    var inp = this.elements[j];
    if (inp.options) {
     d[inp.name] = inp.options[inp.selectedIndex].value;
    } else {
     d[inp.name] = inp.value;
    }
   }
   if (this.submitter != undefined && this.submitter.name) { d[this.submitter.name] = this.submitter.value; }

   var display_div = null;
   for (var j = 0 ; j < this.children.length; j++) {
    if (this.children[j].className == 'ajax_result') display_div = this.children[j];
   }

   if (display_div == null) return true;

   var f = function(http) {
       display_div.innerHTML = "Result: " + http.responseText;
   };

   util.ajax_async( this.action, d, f );
   return false;
  };
 }
};
