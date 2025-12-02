
var html_string = '<svg style="width:100%;height:400px"></svg>';
var html_string_analytics = '<svg style="width:100%;height:100%"></svg>';
var chart_scripts = {};
var chart_instances = {};

function cleanupChart(graph_key) {
   d3.selectAll('.nvtooltip').remove();

   const containerId = 'chart_container_' + graph_key;
   const container = document.getElementById(containerId);
   if (container) {
      const svg = container.querySelector('svg');
      if (svg) {
         d3.select(svg).on('.zoom', null);
         d3.select(svg).selectAll('*').on('.nv', null);
      }
   }

   if (chart_instances[graph_key]) {
      delete chart_instances[graph_key];
   }

   if (window.nv && window.nv.graphs) {
      window.nv.graphs = window.nv.graphs.filter(function(g) {
         return g && g.container && g.container.id !== containerId;
      });
   }
}

function getChartParamsFromUrl(graph_key) {
   const urlParams = new URLSearchParams(window.location.search);
   const params = {};
   const prefix = graph_key + '_';

   for (const [key, value] of urlParams.entries()) {
      if (key.startsWith(prefix)) {
         const paramName = key.substring(prefix.length);
         if (paramName.startsWith('select_box_') || paramName.startsWith('time_')) {
            params[paramName] = value;
         }
      }
   }

   return params;
}

function buildChartUrlParams(formData, graph_key) {
   const formParams = new URLSearchParams(formData);
   const urlParams = new URLSearchParams();
   urlParams.set('show', graph_key);

   for (const [key, value] of formParams.entries()) {
      if (key !== 'csrfmiddlewaretoken' && key !== 'graph_key' &&
          (key.startsWith('select_box_') || key.startsWith('time_'))) {
         urlParams.set(graph_key + '_' + key, value);
      }
   }

   return urlParams;
}

function updateUrlWithChartParams(graph_key, formData) {
   const urlParams = new URLSearchParams(window.location.search);
   const prefix = graph_key + '_';

   const keysToDelete = [];
   for (const [key, value] of urlParams.entries()) {
      if (key.startsWith(prefix)) {
         keysToDelete.push(key);
      }
   }
   keysToDelete.forEach(key => urlParams.delete(key));

   const chartParams = buildChartUrlParams(formData, graph_key);
   chartParams.forEach((value, key) => {
      if (key !== 'show') {
         urlParams.set(key, value);
      }
   });

   const newUrl = window.location.pathname + '?' + urlParams.toString();
   window.history.replaceState({}, '', newUrl);
}

function populateFormFromUrl(form, graph_key) {
   const params = getChartParamsFromUrl(graph_key);

   for (const [key, value] of Object.entries(params)) {
      const input = form.find('[name="' + key + '"]');
      if (input.length > 0) {
         input.val(value);
      }
   }
}

function updateAnalyticsLink(formElement, graph_key) {
   const analyticsLink = formElement.find('a[href*="analytics"]');

   if (analyticsLink.length > 0) {
      const urlParams = buildChartUrlParams(formElement.serialize(), graph_key);
      const baseUrl = analyticsLink.attr('href').split('?')[0];
      const newHref = baseUrl + '?' + urlParams.toString();
      analyticsLink.attr('href', newHref);
   }
}

function loadChart(data, graph_key, reload, is_analytics){
   function storeToChartScripts(data_str) {
      return function(f_data, textStatus, jqXHR) {
            data.removeClass("loading");
            console.log("call " + data_str);
            chart_scripts[data_str] = loadChartScript;
      };
   };

   data_str = data.serialize();

   if(is_analytics) {
      updateUrlWithChartParams(graph_key, data_str);
   }

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
   var is_analytics = data.closest('.chrt_flex').length > 0;

   cleanupChart(graph_key);
   $("#chart_container_" + graph_key).empty().append(is_analytics ? html_string_analytics : html_string);

   updateAnalyticsLink(data, graph_key);
   loadChart(data, graph_key, reload, is_analytics);
}

function loadAnalyticsChart(chart_key){
   const chartElement = $("#chart_element_" + chart_key);

   if(chartElement.hasClass("notloaded")) {
      $('body').addClass("loading");
      $('.admin_charts').hide();
      chartElement.load("{% url "chart-analytics-without-key" %}" + chart_key + "?analytics_chart=true", function(){
         $(this).removeClass('notloaded');
         $(this).addClass('loaded');

         const form = $(this).find('form.stateform:visible');
         populateFormFromUrl(form, chart_key);
         updateAnalyticsLink(form, chart_key);

         form.each(loadAnchor);
         $('body').removeClass("loading");
      });
   } else {
      $('.admin_charts').hide();

      const form = chartElement.find('form.stateform:visible');
      populateFormFromUrl(form, chart_key);
      updateAnalyticsLink(form, chart_key);

      form.each(loadAnchor);
   }

   chartElement.show();
}

function loadAdminChart(chart_key){
   $("#chart_element_" + chart_key + ".notloaded").load("{% url "chart-analytics-without-key" %}" + chart_key, function(){
      $(this).removeClass('notloaded');
      $(this).addClass('loaded');

      const form = $(this).find('form.stateform:visible');
      populateFormFromUrl(form, chart_key);
      updateAnalyticsLink(form, chart_key);

      form.each(loadAnchor);
   });
   $("#chart_element_" + chart_key).show();
}

function downloadCSV(event){
   event.preventDefault();
   var graph_key = $(this).data('graph-key');
   var form = $(this).closest('form.stateform');
   var formData = form.serialize();
   var baseUrl = "{% url 'chart-csv' 'PLACEHOLDER' %}".replace('PLACEHOLDER', graph_key);
   var downloadUrl = baseUrl + '?' + formData;
   window.location.href = downloadUrl;
}

defer( function(){
   $( document ).ready(function() {

      $('body').on('change', '#load_on_change:checked ~ .chart-input', loadAnchor);
      $('body').on('click', '.reload', loadAnchor);
      $('body').on('click', '.download-csv', downloadCSV);
      $('form.stateform:visible').each(loadAnchor);
   });
});
