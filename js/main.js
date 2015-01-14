// For debugging in the console
aryAttemptGraph = [];
aryCGradeGraph = [];
aryGradeGraph = [];

buildGraphs = function(data) {
  var container = d3.select(".ksm-container");
  var graphWidth = 1000;
  var graphHeight = 250
  for (var i in data) {
    probData = data[i];

    divMain = container.append("div")
      .attr("id", "main_"+i)
      .style("position", "relative")
      .style("width", graphWidth + 100);
    
    divMain.append("h2").text(probData["problem_id"]);

    // Attempt stuff
    divMain.append("p").text("Number of Students with a max attempt X.");

    divTooltip = divMain.append("div")
      .attr("class", "tooltip")
      .attr("id", "tt_attempt_"+i);

    divAttemptGraph = divMain.append("div")
      .attr("class", "problem_attempts")
      .attr("id", "dg_attempt_"+i);

    param = {
      data: probData["attempt_data"],
      width: graphWidth,
      height: graphHeight,
      tag: "attempt_"+i,
      bLegend: false,
    };

    barGraph = ksm_d3CreateStackedBarGraph(
      param, divAttemptGraph.append("svg"), divTooltip
    );

    barGraph.scale.stackColor.range(["#555555","#555555"]);
    
    barGraph.drawGraph();

    aryAttemptGraph[i] = barGraph;

    // Grade stuff
    // Student count for each distribution
    divMain.append("p").text("Number of Students with percent grade (color) on their Xth attempt.");
    divTooltip = divMain.append("div")
      .attr("class", "tooltip")
      .attr("id", "tt_grade_count_"+i);

    divCGradeGraph = divMain.append("div")
      .attr("class", "problem_grade_count")
      .attr("id", "dg_grade_count_"+i);

    param = {
      data: probData["grade_count_data"],
      width: graphWidth,
      height: graphHeight,
      tag: "grade_count_"+i,
    };

    barCGraph = ksm_d3CreateStackedBarGraph(
      param, divCGradeGraph.append("svg"), divTooltip
    );

    barCGraph.scale.stackColor.domain([0,50,100]).range(["#e13f29","#cccccc","#17a74d"]);
    barCGraph.drawGraph();

    aryCGradeGraph[i] = barCGraph;

    // Grade Distribution Graph
    divMain.append("p").text("Fraction of Students with percent grade (color) on their Xth attempt. (Normalized version of above graph)");
    divTooltip = divMain.append("div")
      .attr("class", "tooltip")
      .attr("id", "tt_grade_"+i);

    divGradeGraph = divMain.append("div")
      .attr("class", "problem_grade")
      .attr("id", "dg_grade_"+i);

    param = {
      data: probData["grade_data"],
      width: graphWidth,
      height: graphHeight,
      tag: "grade_"+i,
    };

    barGraph = ksm_d3CreateStackedBarGraph(
      param, divGradeGraph.append("svg"), divTooltip
    );

     barGraph.scale.stackColor.domain([0,50,100]).range(["#e13f29","#cccccc","#17a74d"]);
    barGraph.drawGraph();
    barGraph.yAxisLabel.text("Fraction of Students")

    aryGradeGraph[i] = barGraph;

  }
}