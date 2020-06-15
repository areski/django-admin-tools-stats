
var html_string = '<svg style="width:100%;height:400px"></svg>';
var html_string_analytics = '<svg style="width:100%;height:100%"></svg>';
var chart_scripts = {};

function loadChart(data, graph_key){
   var storeToChartScripts = function(data_str) {
      return function(data, textStatus, jqXHR) {
            console.log("call " + data_str);
            chart_scripts[data_str] = loadChartScript;
      };
   };

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
         success: storeToChartScripts(data_str)
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

function loadAnchor(){
   var data = $(this).closest('form.stateform');
   var graph_key = data.children(".hidden_graph_key").first().val();
   var is_analytics = $(this).parent().hasClass("chrt_flex");
   if($(this).hasClass('select_box_chart_type') || $(this).hasClass('stateform')){
      $("#chart_container_" + graph_key).empty().append(is_analytics ? html_string_analytics : html_string);
   };
   loadChart(data, graph_key);
}

defer( function(){
   $( document ).ready(function() {

      $('body').on('change', '.chart-input', loadAnchor);
      $('form.stateform:visible').each(loadAnchor);
   });
});
