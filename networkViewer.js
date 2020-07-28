
//Variables
let HOPS = {
    0: {
        background: "#577590",
        fontColor: "white",
        title: "Hub",
        classSuffix: "hub",
        image: "images/hub.png"
    },
    1: {
        background: "#43aa8b",
        fontColor: "black",
        image: "images/node.png"
    },
    2: {
        background: "#90be6d",
        fontColor: "black",
        image: "images/node.png"
    },
    3: {
        background: "#f9c74f",
        fontColor: "black",
        image: "images/node.png"
    },
    4: {
        background: "#f8961e",
        fontColor: "black",
        image: "images/node.png"
    },
    "-1": {
        background: "#f94144",
        fontColor: "white",
        title: "Not connected",
        classSuffix: "not-connected",
        image: "images/alert.png"
    }
};

const ATTRIBUTES_MAPPING = {
    "entity_id": {
        title: "Entity Id",
        breakAfter: true
    },
    "product_name": {
        title: "Product name",
        breakAfter: true
    },
    "manufacturer_name": {
        title: "Manufacturer",
        breakAfter: false
    },
    "state": {
        title: "State",
        breakAfter: false
    },
    "query_stage": {
        title: "Query stage",
        breakAfter: false
    },
    "battery_level": {
        title: "Battery level",
        breakAfter: false
    },
    "application_version": {
        title: "Version",
        breakAfter: false
    }
};

const CAPABILITY_INFO = {
    "primaryController": {
        image: "primaryController.png",
        title: "Hub"
    },
    "zwave_plus": {
        image: "zwaveplus.png",
        title: "Z-Wave Plus"
    },
    "beaming": {
        image: "beaming.png",
        title: "Beaming"
    },
    "listening": {
        image: "listening.png",
        title: "Listening"
    },
    "is_awake": {
        image: "awake.png",
        title: "Awake"
    },
    "routing": {
        image: "routing.png",
        title: "Routing"
    },
    "is_failed": {
        image: "failed.png",
        title: "Failed"
    }
};

const options = {
    edges: {
        smooth: true
    },
    nodes: {
        shape: 'circularImage',
        size: 32,
        shapeProperties: {
            useImageSize: true,
            useBorderWithImage: false,
            interpolation: false,
            coordinateOrigin: 'center'
        },
        widthConstraint: {
            maximum: 60
        },
    },
    layout: {
        hierarchical: {
            direction: "UD",
            nodeSpacing: 100,
            treeSpacing: 100,
            levelSeparation: 190,
            sortMethod: "directed"
        }
    },
    physics: {
        enabled: false,
        hierarchicalRepulsion: {
            centralGravity: 0,
            nodeDistance: 150,
        }
    },
    interaction: {
        hover: true,
        navigationButtons: true
    }
};


// Build graph
const networkItems = [];
let networkView = null;

const checkCapability = (capabilities, attributes, key) => {
    const capability = attributes[key];

    if(capability !== undefined&& eval(capability) === true) {
        capabilities.push(key);
    }
};

const getCapabilities = (selectedItem) => {
    const attributes = selectedItem.entity.attributes;

    let capabilities = attributes.capabilities;

    if (capabilities === undefined) {
        capabilities = [];
    }

    const additionalCapabilities = [
        "is_awake",
        "is_failed",
        "is_ready",
        "is_zwave_plus"
    ];

    additionalCapabilities.forEach(c => {
        checkCapability(capabilities, attributes, c);
    });

    return capabilities;
};

const getItem = (node_id) => {
    return networkItems.filter(e => e.id === node_id)[0];
};

const updateNodeData = (node) => {
    const hop = node.hop;
    const currentHopSettings = HOPS[hop];

    node["label"] = `[${node.id}] ${node.name}`;

    node["image"] = currentHopSettings.image;

    node["color"] = currentHopSettings.background;
    node["font"] = {
        color: "white"
    };

    node["chosen"] = {
        label: true,
        node: changeChosenNodeColor
    }

};

const changeChosenNodeColor = (values, id, selected, hovering) => {
    if (selected) {
        values.color = "#00a8e8";
    }
};

// UI
const loadHopsLegend = () => {
    const container = document.getElementById("hops-legend");

    const hopLegendTitle = document.createElement("div");
    hopLegendTitle.innerText = "Legend";
    hopLegendTitle.className = "sidebar-section-title";
    container.appendChild(hopLegendTitle);

    const hops = Object.keys(HOPS);

    hops.forEach(h => {
        const currentHop = HOPS[h];
        const text = currentHop.title === undefined ? `Hop ${h}` : currentHop.title;
        const currentHopClassSuffix = currentHop.classSuffix === undefined ? `hop-${h}` : currentHop.classSuffix;

        const hopContent = document.createElement("div");
        hopContent.className = "sidebar-section-content";

        const hopContentBox = document.createElement("div");
        hopContentBox.innerHTML = "&nbsp;";
        hopContentBox.className = `legend-box legend-box-${currentHopClassSuffix}`;
        hopContent.appendChild(hopContentBox);

        const hopContentText = document.createElement("div");
        hopContentText.className = "legend-title";
        hopContentText.innerText = text;
        hopContent.appendChild(hopContentText);

        container.appendChild(hopContent);
    });
};

const loadNetworkView = () => {
    const networkEdges = [];

    networkItems.forEach(n => {
       n.edges.forEach(e => {
           if(e.type === "parent") {
               networkEdges.push({
                   from: e.id,
                   to: e.toNodeId,
                   width: 1,
                   dashes: true
               });
           }
       });
    });

    // create an array with nodes
    const nodes = new vis.DataSet(networkItems);

    // create an array with edges
    const edges = new vis.DataSet(networkEdges);

    const data = {
        nodes: nodes,
        edges: edges
    };

    const container = document.getElementById("network");

    // create a network
    networkView = new vis.Network(container, data, options);

    networkView.on("click", onSelect);
    networkView.selectNodes([1]);

    onSelect();
};

const setNeighbors = (selectedItem) => {
    const neighbors = selectedItem.neighbors;
    const divNeighbors = document.createElement("div");
    const hasNeighbors = neighbors !== undefined && neighbors !== null && neighbors.length > 0;

    const orderedNeighbors = {};

    if (hasNeighbors) {
        neighbors.map(n => networkItems.filter(i => i.id === n)[0])
            .forEach(i => {
                let hopNeighbors = orderedNeighbors[i.hop];

                if(hopNeighbors === undefined) {
                    hopNeighbors = [];
                    orderedNeighbors[i.hop] = hopNeighbors;
                }

                hopNeighbors.push(i);
            });

        const hopKeys = Object.keys(HOPS).sort();

        hopKeys.forEach(hk => {
            const items = orderedNeighbors[hk];

            if(items !== undefined) {
                items.forEach(n => {
                    const divNeighbor = document.createElement("div");
                    divNeighbor.className = "node-neighbor-item";
                    divNeighbor.style.color = n.color;
                    divNeighbor.innerText = n.label;
                    divNeighbor["nodeId"] = n.id;

                    divNeighbor.onclick = neighborClicked;

                    divNeighbors.appendChild(divNeighbor);
                });
            }
        });
    }

    const element = document.getElementById('node-neighbors-content');
    while (element.firstChild) {
        element.removeChild(element.lastChild);
    }

    element.appendChild(divNeighbors);

    const neighborSection = document.getElementById('node-neighbors');
    neighborSection.style.display = hasNeighbors ? "block" : "none";
};

const setDetailsItem = (container, title, content, breakAfter) => {
    const div = document.createElement("div");
    div.className = "node-details-content-item";

    const titleDiv = document.createElement("div");
    titleDiv.innerHTML = title + ":";
    titleDiv.className = "node-details-content-item-title" + (breakAfter ? "" : " node-details-content-item-no-break");
    div.appendChild(titleDiv);

    const contentDiv = document.createElement("div");
    contentDiv.innerHTML = content;

    if (!breakAfter){
        contentDiv.className = "node-details-content-item-no-break";
    }

    div.appendChild(contentDiv);

    container.appendChild(div);
};

const setDetails = (selectedItem) => {
    const nodeName = document.getElementById('node-details-title');
    nodeName.innerText = selectedItem.label;

    const attr_keys = Object.keys(ATTRIBUTES_MAPPING);
    const attributes = selectedItem.entity.attributes;
    const availableAttributes = {};

    attr_keys.forEach(ak => {
        availableAttributes[ak] = attributes[ak];
    });

    availableAttributes["entity_id"] = selectedItem.entity.entity_id;
    availableAttributes["state"] = selectedItem.entity.state;

    const nodeDetailsContent = document.getElementById('node-details-content');
    while (nodeDetailsContent.firstChild) {
        nodeDetailsContent.removeChild(nodeDetailsContent.lastChild);
    }

    const div = document.createElement("div");
    div.className = "";

    attr_keys.forEach(k => {
        const attrDetails = ATTRIBUTES_MAPPING[k];
        const attrValue = availableAttributes[k];

        if (attrValue !== undefined && attrValue !== "Unknown") {
            setDetailsItem(div, attrDetails.title, attrValue, attrDetails.breakAfter);
        }
    });

    nodeDetailsContent.appendChild(div);
};

const setCapabilityIcons = (selectedItem) => {
    const capabilities = getCapabilities(selectedItem);

    const capabilityImageKeys = Object.keys(CAPABILITY_INFO);

    const availableCapabilities = capabilityImageKeys.filter(ck => capabilities !== undefined && capabilities.indexOf(ck) > -1);

    const divIcons = document.createElement("div");
    divIcons.className = "node-details-content-item";

    availableCapabilities.forEach(ck => {
        const img = document.createElement("img");
        const capabilityInfo = CAPABILITY_INFO[ck];

        img.src = `images/${capabilityInfo.image}`;
        img.className = "node-capability-icon";
        img.title = capabilityInfo.title;

        divIcons.appendChild(img);
    });

    const element = document.getElementById('node-details-content');
    element.appendChild(divIcons);
};

const selectedItemChanged = (selectedItem) => {
    const sidebar = document.getElementById("sidebar");

    const isSelected = selectedItem !== null;
    sidebar.style.display = isSelected ? "block" : "none";

    if (!isSelected) {
        return;
    }

    setDetails(selectedItem);
    setCapabilityIcons(selectedItem);
    setNeighbors(selectedItem);
};

// UI Events
const onSelect = (eventData, callback) => {
    const selectedNodes = eventData === undefined ? [] : eventData.nodes;
    let selectedItem = networkItems[0];

    if (selectedNodes.length === 0) {
        networkView.selectNodes([1]);
    }
    else {
        const firstNode = selectedNodes[0];
        selectedItem = getItem(firstNode);
    }

    selectedItemChanged(selectedItem);
};

const neighborClicked = (e) => {
    const nodeId = e.target.nodeId;

    networkView.selectNodes([nodeId]);

    const selectedItem = getItem(nodeId);

    selectedItemChanged(selectedItem);
};

// Initialize
const initialize = (nodes) => {
    nodes.forEach(n => {
        updateNodeData(n);

        networkItems.push(n);
    });

    loadHopsLegend();
    loadNetworkView();
};