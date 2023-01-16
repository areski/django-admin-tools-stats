
var html_string = '<svg style="width:100%;height:400px"></svg>';
var html_string_analytics = '<svg style="width:100%;height:100%"></svg>';
var chart_scripts = {};

function loadChart(data, graph_key, reload){
   function storeToChartScripts(data_str) {
      return function(f_data, textStatus, jqXHR) {
            data.removeClass("loading");
            console.log("call " + data_str);
            chart_scripts[data_str] = loadChartScript;
      };
   };

   data_str = data.serialize();

   if(!reload && data_str in chart_scripts){
      data.removeClass("loading");
      console.log("run " + data_str);
      chart_scripts[data_str]();
   } else {
      url = "{% url 'chart-data' %}" + graph_key + "/";
      if(reload)
         reload_str = "&" + reload + "=true"
      else
         reload_str = ""
      $.ajax({
         dataType: "script",
         'url': url,
         'data': data_str + reload_str,
         success: storeToChartScripts(data_str),
         error: function(){
             alert("Error during chart loading.");
             data.removeClass("loading");
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

function loadAnchor(){
   if($(this)[0].id == 'reload' || $(this)[0].id == 'reload_all')
      reload = $(this)[0].id;
   else
      reload = false;
   var data = $(this).closest('form.stateform');
   data.addClass("loading");
   var graph_key = data.find(".hidden_graph_key").first().val();
   var is_analytics = $(this).parent().hasClass("chrt_flex");
   if($(this).hasClass('select_box_chart_type') || $(this).hasClass('stateform')){
      $("#chart_container_" + graph_key).empty().append(is_analytics ? html_string_analytics : html_string);
   };
   loadChart(data, graph_key, reload);
}

function loadAnalyticsChart(chart_key){
   if($("#chart_element_" + chart_key + ".notloaded").length)
      $('body').addClass("loading");
   $('.admin_charts').hide();
   $("#chart_element_" + chart_key + ".notloaded").load("{% url "chart-analytics-without-key" %}" + chart_key, function(){
      $(this).removeClass('notloaded');
      $(this).addClass('loaded');
      $(this).find('form.stateform:visible').each(loadAnchor);
      $('body').removeClass("loading");
   });
   $("#chart_element_" + chart_key).show();
}

defer( function(){
   $( document ).ready(function() {

      $('body').on('change', '#load_on_change:checked ~ .chart-input', loadAnchor);
      $('body').on('click', '.reload', loadAnchor);
      $('form.stateform:visible').each(loadAnchor);
   });
});
