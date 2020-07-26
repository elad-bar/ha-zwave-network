
const HOPS = {
    0: {
        background: "#577590",
        fontColor: "white",
        title: "Hub",
        classSuffix: "hub"
    },
    1: {
        background: "#43aa8b",
        fontColor: "black"
    },
    2: {
        background: "#90be6d",
        fontColor: "black"
    },
    3: {
        background: "#f9c74f",
        fontColor: "black"
    },
    4: {
        background: "#f8961e",
        fontColor: "black"
    },
    "-1": {
        background: "#f94144",
        fontColor: "white",
        title: "Not connected",
        classSuffix: "not-connected"
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
}


const options = {
    edges: {
        smooth: true
    },
    nodes: {
        shape: 'box',
        widthConstraint: {
            maximum: 60
        },
    },
    layout: {
        hierarchical: {
            direction: "UD",
            nodeSpacing: 100,
            treeSpacing: 190,
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

const networkItems = [];
let networkView = null;

const checkCapability = (capabilities, attributes, key) => {
    const capability = attributes[key];

    if(capability !== undefined&& eval(capability) === true) {
        capabilities.push(key);
    }
}

const getCapabilities = (selectedItem) => {
    const attributes = selectedItem.data.attributes;

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
}

const setNeighbors = (selectedItem) => {
    const neighbors = selectedItem.neighbors;
    const divNeighbors = document.createElement("div");
    const orderedNeighbors = {};

    neighbors.map(n => networkItems.filter(i => i.id === n)[0])
        .forEach(i => {
            let hopNeighbors = orderedNeighbors[i.hop];

            if(hopNeighbors === undefined) {
                hopNeighbors = [];
                orderedNeighbors[i.hop] = hopNeighbors;
            }

            hopNeighbors.push(i);
        });

    hopKeys = Object.keys(HOPS).sort();

    hopKeys.forEach(hk => {
        items = orderedNeighbors[hk];

        if(items !== undefined) {
            items.forEach(n => {
                const divNeighbor = document.createElement("div");
                divNeighbor.className = "node-neighbor-item";
                divNeighbor.style.color = n.color;
                divNeighbor.innerText = n.label;
                divNeighbor["nodeId"] = n.id;

                divNeighbor.onclick = neighborClicked

                divNeighbors.appendChild(divNeighbor);
            });
        }
    });

    const element = document.getElementById('node-neighbors-content');
    while (element.firstChild) {
        element.removeChild(element.lastChild);
    }

    element.appendChild(divNeighbors);
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
}

const setDetails = (selectedItem) => {
    const nodeName = document.getElementById('node-details-title');
    nodeName.innerText = selectedItem.label;

    const attr_keys = Object.keys(ATTRIBUTES_MAPPING);
    const attributes = selectedItem.data.attributes;
    const availableAttributes = {};

    attr_keys.forEach(ak => {
        availableAttributes[ak] = attributes[ak];
    });

    availableAttributes["entity_id"] = selectedItem.data.entity_id;
    availableAttributes["state"] = selectedItem.data.state;

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

const loadHopsLegend = () => {
    const container = document.getElementById("hops-legend");

    const hopLegendTitle = document.createElement("div");
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
        hopContentBox.className = `legend-box legend-box-${currentHopClassSuffix}`;
        hopContent.appendChild(hopContentBox);

        const hopContentText = document.createElement("div");
        hopContentText.className = "legend-title";
        hopContentText.innerText = text;
        hopContent.appendChild(hopContentText);

        container.appendChild(hopContent);
    });
};

const neighborClicked = (e) => {
    const nodeId = e.target.nodeId;

    networkView.selectNodes([nodeId]);

    const selectedItem = getItem(nodeId);

    selectedItemChanged(selectedItem);
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

const getEntityEdges = (node_id, neighbors) => {
    return neighbors === undefined ?
        [] :
        neighbors.map(n => {
            return {
                from: node_id,
                to: n,
                width: 1,
                dashes: true
            };
        });
};

const getItem = (node_id) => {
    return networkItems.filter(e => e.id === node_id)[0];
};

const setItemHop = (currentItem) => {
    const currentHop = currentItem.hop;

    if (currentItem.neighbors !== undefined) {
        const neighbors = currentItem.neighbors.map(n => getItem(n));

        neighbors
            .filter(n => n.hop === -1 || n.hop > currentHop + 1)
            .forEach(n => {
                n.hop = currentHop + 1;

                setItemHop(n);
            });
    }
};

const setItemsHop = () => {
    networkItems.filter(i => i.hop > -1)
        .forEach(i => setItemHop(i));
};

const setInitialHop = (entities) => {
    entities.forEach(e => {
        const attributes = e.attributes;

        if(attributes.neighbors === undefined) {
            attributes.neighbors = [];
            attributes.neighbors.push(1);
        }

        const neighbors = attributes.neighbors;
        const capabilities = attributes.capabilities;

        const isPrimaryController = capabilities !== undefined && capabilities.indexOf("primaryController") > -1;

        attributes["hop"] = isPrimaryController ? 0 : neighbors === undefined ? 1 : -1;
    });
};

const loadNetworkItems = (entities) => {
    entities.forEach(entity => {
        const attributes = entity.attributes;
        const node_id = attributes.node_id;
        const neighbors = attributes.neighbors;
        const name = attributes.friendly_name;
        const hop = attributes.hop;
        const currentHop = HOPS[hop];

        networkItems.push({
            id: node_id,
            label: `[${node_id}] ${name}`,
            hop: attributes.hop,
            neighbors: neighbors,
            color: currentHop.background,
            font: {
                color: currentHop.fontColor
            },
            edges: getEntityEdges(node_id, neighbors),
            data: entity
        });
    });

    setItemsHop();
};

const getEdges = () => {
    const allEdges = [];
    const filteredEdges = [];
    let highestHop = -1;

    networkItems.forEach(i => {
        if (i.hop > highestHop) {
            highestHop = i.hop + 1;
        }

        i.edges.forEach(e => allEdges.push(e));
    });

    allEdges.forEach(e => {
        const fromItem = getItem(e.from);
        const toItem = getItem(e.to);

        if (fromItem.hop > -1 && fromItem.hop < toItem.hop) {
            filteredEdges.push(e);
        }

    });

    return filteredEdges;
};

const fixItemData = () => {
    networkItems.forEach(i => {
        const currentHop = HOPS[i.hop];

        if(currentHop === undefined) {
            currentHop = HOPS["-1"];
        }

        i.color = currentHop.background;
        i.font.color = currentHop.fontColor;
    });
};

const loadNetworkView = (networkEdges) => {
    // create an array with nodes
    const nodes = new vis.DataSet(networkItems);

    // create an array with edges
    const edges = new vis.DataSet(networkEdges);

    const data = {
        nodes: nodes,
        edges: edges
    };

    const container = document.getElementById("network")

    networkView = new vis.Network(container, data, options);

    networkView.on("click", onSelect);
    networkView.selectNodes([1]);

    onSelect();
};

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

const initialize = (entities) => {
    loadHopsLegend();
    setInitialHop(entities);

    loadNetworkItems(entities);
    const edges = getEdges();

    fixItemData();

    loadNetworkView(edges);
};