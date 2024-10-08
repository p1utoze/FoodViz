const svg = d3.select("svg");
const width = +svg.attr("width");
const height = +svg.attr("height");
const tooltip = d3.select(".tooltip");

async function getData() {
    try {
        return await d3.csv('../../data/food-types.csv');
    } catch (error) {
        console.error("Error loading CSV:", error);
        throw error;
    }
}

async function initializeVisualization() {
    const csvData = await getData();
    const data = csvData.map((k) => ({
        id: k.grup,  // Using 'grup' as id
        r: +k.items, // Convert to number
        name: k.grup,
        url: k.url,
        x: Math.random() * width,
        y: Math.random() * height,
        vx: 1,
        vy: 1,
    }));

    console.log("Processed data:", data);

    // Color scale
    const color = d3.scaleOrdinal(d3.schemeCategory10);

    // Create the simulation
    const simulation = d3.forceSimulation(data)
        .force("x", d3.forceX(width / 2).strength(0.05))
        .force("y", d3.forceY(height / 2).strength(0.05))
        .force("charge", d3.forceManyBody().strength(-10).distanceMin(d => d.r + 2))
        .force("collide", d3.forceCollide().radius(d => d.r + 1).iterations(2));

    // Create the bubbles
    const bubbles = svg.selectAll("g")
        .data(data)
        .enter().append("g")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended))
        .on("mouseover", showTooltip)
        .on("mousemove", moveTooltip)
        .on("mouseout", hideTooltip);

    bubbles.append("circle")
        .attr("r", d => d.r)
        .attr("fill", (d, i) => color(i));

    bubbles.append("image")
        .attr("href", d => d.url)  // Use the URL from the CSV data
        .attr("width", d => 1.5 * d.r)
        .attr("height", d => 1.5 * d.r);

    let draggedNode = null;

    // Update bubble positions on each tick of the simulation
    simulation.on("tick", () => {
        bubbles.select("circle")
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);
        bubbles.select("image")
            .attr("x", d => d.x - d.r * 0.75)
            .attr("y", d => d.y - d.r * 0.75);

        // Your existing collision detection code here
        // ...
    });

    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.4).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
        draggedNode = null;
    }

    function showTooltip(event, d) {
        tooltip.style("opacity", 1)
            .html(`Name: ${d.name}<br>Items: ${d.r}`);
        moveTooltip(event);
    }

    function moveTooltip(event) {
        tooltip.style("left", (event.pageX + 10) + "px")
               .style("top", (event.pageY - 10) + "px");
    }

    function hideTooltip() {
        tooltip.style("opacity", 0);
    }
}

// Call the function to initialize the visualization
initializeVisualization().catch(error => console.error('Failed to initialize visualization:', error));