
const HOP_COLORS = {
    "-1": {
        background: "#f94144",
        fontColor: "white"
    },
    0: {
        background: "#577590",
        fontColor: "white"
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
    }
};

const ATTRIBUTES_MAPPING = {
    "manufacturer_name": "Manufacturer",
    "product_name": "Product name",
    "query_stage": "Query stage",
    "application_version": "Version",
    "capabilities": "Capabilities",
    "is_awake": "Awake",
    "is_failed": "Failed",
    "is_ready": "Ready",
    "is_zwave_plus": "Z-Wave Plus"
};


const options = {
    edges: {
        smooth: true
    },
    nodes: {
        shape: 'box',
        widthConstraint: {
            maximum: 50
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

const selectedItemChanged = (selectedItem) => {
    const isSelected = selectedItem !== null;
    sidebar.style.display = isSelected ? "block" : "none";

    if (!isSelected) {
        return;
    }

    setText('node-name', selectedItem.label);

    const attr_keys = Object.keys(ATTRIBUTES_MAPPING);
    const attributes = selectedItem.data.attributes;
    const detailItems = [];
    const neighborItems = [];

    detailItems.push(`<span><span class="node-details-content-item-title">Entity Id:</span></br> ${selectedItem.data.entity_id}</span>`);
    detailItems.push(`<span><span class="node-details-content-item-title">State:</span></br> ${selectedItem.data.state}</span>`);

    attr_keys.forEach(k => {
        const attrName = ATTRIBUTES_MAPPING[k];
        const attrValue = attributes[k];

        const detailItem = `<span><span class="node-details-content-item-title">${attrName}:</span></br> ${attrValue}</span>`;

        detailItems.push(detailItem);

    });

    setTextItems('node-details-content', detailItems);

    const neighbors = attributes.neighbors;

    neighbors.forEach(n => {
        const neighbor = networkItems.filter(i => i.id === n)[0];

        neighborItems.push(`${neighbor.label}`);
    });

    setTextItems('node-neighbors-content', neighborItems);
};

const setText = (elementId, text) => {
    const element = document.getElementById(elementId);
    element.innerText = text;
};

const setTextItems = (elementId, textItems) => {
    const element = document.getElementById(elementId);
    while (element.firstChild) {
        element.removeChild(element.lastChild);
    }

    const div = document.createElement("div");

    textItems.forEach(i => {
        const item = document.createElement("item");
        item.innerHTML = i;
        div.appendChild(item);

        const br = document.createElement("br");
        div.appendChild(br);
    });

    element.appendChild(div);
};

const getEntityEdges = (node_id, neighbors) => {
    return neighbors === undefined ?
        [] :
        neighbors.map(n => {
            return {
                from: node_id,
                to: n,
                width: 1
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

        const isPrimaryController = capabilities.indexOf("primaryController") > -1;

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
        const colorSet = HOP_COLORS[hop];

        networkItems.push({
            id: node_id,
            label: `[${node_id}] ${name}`,
            hop: attributes.hop,
            neighbors: neighbors,
            color: colorSet.background,
            font: {
                color: colorSet.fontColor
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

        if (fromItem.hop < toItem.hop) {
            filteredEdges.push(e);
        }

    });

    return filteredEdges;
};

const fixItemData = () => {
    networkItems.forEach(i => {
        const colorSet = HOP_COLORS[i.hop];

        i.color = colorSet.background;
        i.font.color = colorSet.fontColor;
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
    setInitialHop(entities);

    loadNetworkItems(entities);
    const edges = getEdges();

    fixItemData();

    loadNetworkView(edges);
};