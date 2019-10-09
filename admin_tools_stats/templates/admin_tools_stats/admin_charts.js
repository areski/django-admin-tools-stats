
var html_string = '<svg style="width:{{chart_width}};height:{{chart_height}}px;"></svg>';
var chart_scripts = {};

function loadChart(data, graph_key){
   data_str = data.serialize();

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
         var graph_key = data.children(".hidden_graph_key").first().val();
         if($(this).hasClass('select_box_chart_type') || $(this).hasClass('stateform')){
            $("#chart_container_" + graph_key).empty().append(html_string);
         };
         loadChart(data, graph_key);
      }

      $('body').on('change', '.chart-input', loadAnchor);
      $('form.stateform').each(loadAnchor);
   });
});
