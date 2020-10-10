
//Variables
const REFRESH_INTERVAL = 5 * 1000;

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
        image: "images/node-online.png"
    },
    2: {
        background: "#90be6d",
        fontColor: "black",
        image: "images/node-online.png"
    },
    3: {
        background: "#f9c74f",
        fontColor: "black",
        image: "images/node-online.png"
    },
    4: {
        background: "#f8961e",
        fontColor: "black",
        image: "images/node-online.png"
    },
    "-1": {
        background: "#f94144",
        fontColor: "white",
        title: "Failed / Not connected",
        classSuffix: "not-connected",
        image: "images/alert.png"
    }
};

const ATTRIBUTES_MAPPING = {
    "product": {
        title: "Product name",
        breakAfter: true
    },
    "manufacturer": {
        title: "Manufacturer",
        breakAfter: false
    },
    "queryStage": {
        title: "Query stage",
        breakAfter: false
    },
    "lastResponseRTT": {
      title: "Response time (MSec)",
      breakAfter: false
    },
    "batteryLevel": {
        title: "Battery level",
        breakAfter: false
    },
    "version": {
        title: "Version",
        breakAfter: false
    },
    "entityCount": {
        title: "Entities",
        breakAfter: false
    }
};

const CAPABILITY_INFO = {
    "isPrimary": {
        image: "primaryController.png",
        title: "Hub"
    },
    "isZWavePlus": {
        image: "zwaveplus.png",
        title: "Z-Wave Plus"
    },
    "isBeaming": {
        image: "beaming.png",
        title: "Beaming"
    },
    "isListening": {
        image: "listening.png",
        title: "Listening"
    },
    "isAwake": {
        image: "awake.png",
        title: "Awake"
    },
    "isRouting": {
        image: "routing.png",
        title: "Routing"
    },
    "isFailed": {
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
            interpolation: false
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
let  networkItems = [];
let networkView = null;

const getCapabilities = (selectedItem) => {
    const capabilities = [];

    const capabilityKeys = Object.keys(CAPABILITY_INFO);

    capabilityKeys.forEach(c => {
        const capability = selectedItem[c];

        if(capability !== undefined && eval(capability) === true) {
            capabilities.push(c);
        }
    });

    return capabilities;
};

const getItem = (node_id) => {
    return networkItems.filter(e => e.id === node_id)[0];
};

const updateNodeData = (node) => {
    const hop = node.hop;
    let currentHopSettings = HOPS[hop];

    if (currentHopSettings === undefined){
        currentHopSettings = HOPS["-1"]
    }

    if(node.isFailed) {
        currentHopSettings = {
            background: "#f94144",
            fontColor: "white",
            title: "Failed",
            classSuffix: "not-connected",
            image: "images/node-offline.png"
        }
    }

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
    while (container.firstChild) {
        container.removeChild(container.lastChild);
    }

    const hopLegendTitle = document.createElement("div");
    hopLegendTitle.innerText = "Neighbors";
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

        const hopContentNeighbors = document.createElement("div");
        hopContentNeighbors.id = `neighbors-${currentHopClassSuffix}`;
        hopContent.appendChild(hopContentNeighbors);

        container.appendChild(hopContent);
    });
};

const loadNetworkView = () => {
    const networkEdges = [];

    networkItems.filter(n => !n.isFailed)
                .forEach(n => {
       n.edges.forEach(e => {
           if(e.type === "parent") {
               const toNode = getItem(e.toNodeId);

               if (!toNode.isFailed) {

                   networkEdges.push({
                       from: e.id,
                       to: e.toNodeId,
                       width: 1,
                       dashes: true
                   });
               }
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

    const hasNeighbors = neighbors !== undefined && neighbors !== null && neighbors.length > 0;

    const orderedNeighbors = {};
    const hopKeys = Object.keys(HOPS).sort();

    hopKeys.forEach(hk => {
        const currentHop = HOPS[hk];
        const currentHopClassSuffix = currentHop.classSuffix === undefined ? `hop-${hk}` : currentHop.classSuffix;
        const divNeighbors = document.getElementById(`neighbors-${currentHopClassSuffix}`);
        clearChildren(divNeighbors);
    });


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



        hopKeys.forEach(hk => {
            const items = orderedNeighbors[hk];

            if(items !== undefined) {
                const currentHop = HOPS[hk];
                const currentHopClassSuffix = currentHop.classSuffix === undefined ? `hop-${hk}` : currentHop.classSuffix;
                const divNeighbors = document.getElementById(`neighbors-${currentHopClassSuffix}`);

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

const clearChildren = (element) => {
    while (element.firstChild) {
        element.removeChild(element.lastChild);
    }
}

const setDetails = (selectedItem) => {
    const nodeName = document.getElementById('node-details-title');
    nodeName.innerText = selectedItem.label;

    const attr_keys = Object.keys(ATTRIBUTES_MAPPING);

    const availableAttributes = {};

    attr_keys.forEach(ak => {
        availableAttributes[ak] = selectedItem[ak];
    });

    const nodeDetailsContent = document.getElementById('node-details-content');
    clearChildren(nodeDetailsContent);

    const div = document.createElement("div");
    div.className = "";

    attr_keys.forEach(k => {
        const attrDetails = ATTRIBUTES_MAPPING[k];
        const attrValue = availableAttributes[k];

        if (attrValue !== undefined && attrValue !== null && attrValue != "Unknown" && attrValue.toString().length > 0) {

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
    networkItems = [];
    console.log(nodes);

    nodes.forEach(n => {
        updateNodeData(n);

        if(n.device.InstanceID == 1)
        {
            networkItems.push(n);
        }
    });

    if(nodes.length > 0) {
        loadNetworkView();
    }
};

const onLoad = () => {
    loadHopsLegend();

    refresh();
}

const onDebug = () => {
    window.open('/nodes.json')
}

const refresh = () => {
    fetch("nodes.json")
        .then(response => {
            if (!response.ok) throw new Error(response.status);
            return response.json();
        }).then(nodes => {
        //Set hop
        initialize(nodes);

        return nodes;
    }).catch(e => console.log(e));
};