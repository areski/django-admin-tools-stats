
var chart_scripts = {};

function loadChart(data){
   data_str = data.serialize();
   var graph_key = data.children(".hidden_graph_key").first().val();

   if(data_str in chart_scripts){
      console.log("run " + data_str);
      chart_scripts[data_str]();
   } else {
      url = "{% url 'chart-data' %}" + graph_key + "/";
      $.ajax({
         dataType: "script",
         'url': url,
         'data': data.serialize(),
         success: function(){
            console.log("call " + data_str);
            chart_scripts[data_str] = loadChartScript;
         }
      });
   };
}

function defer(method) {
    if (window.jQuery && window.nv) {
        method();
    } else {
        setTimeout(function() { defer(method) }, 50);
    }
}

defer( function(){
   $( document ).ready(function() {
      function loadAnchor(){
         var data = $(this).closest('form.stateform');
         loadChart(data);
      }

      $('.chart-input').closest('form.stateform').change(loadAnchor);
      $('form.stateform').each(loadAnchor);
   });
});
