import {RECEIVE, CHANGE, CONFIG, ADD_ATTRIBUTE_LISTENER,
        REMOVE_ATTRIBUTE_LISTENER} from "./actions";


function deviceStore (state, action) {
    if (!action.data || !action.data.device)
        return state    
    switch (action.type) {
    case RECEIVE:
        return Object.assign({}, state, action.data.device)
    default:
        return state;
    }
}


function domainStore (state, action) {
    if (!action.data || !action.data.domain)
        return state    
    switch (action.type) {
    case RECEIVE:
        return Object.assign({}, state, action.data.domain)
    default:
        return state;
    }
}


function familyStore (state, action) {
    if (!action.data || !action.data.family)
        return state    
    switch (action.type) {
    case RECEIVE:
        return Object.assign({}, state, action.data.family)
    default:
        return state;
    }
}


function memberStore (state, action) {
    if (!action.data || !action.data.member)
        return state    
    switch (action.type) {
    case RECEIVE:
        return Object.assign({}, state, action.data.member)
    default:
        return state;
    }
}



function attributeValueStore (state, action) {
    if (!action.data)
        return state
    switch (action.type) {
    case CHANGE:
        return Object.assign({}, state, action.data);
    default:
        return state;
    }
}


// store for attribute config data
function attributeConfigStore (state, action) {
    if (!action.data)
        return state
    switch (action.type) {
    case CONFIG:
        return Object.assign({}, state, action.data);
    default:
        return state;
    }
}


function propertyStore (state, action) {
    if (!action.data || !action.data.property)
        return state
    switch (action.type) {
    case RECEIVE:
        return Object.assign({}, state, action.data.property);
    default:
        return state;
    }
}


function attributeStore (state, action) {
    if (!action.data || !action.data.attribute)
        return state
    switch (action.type) {
    case RECEIVE:
        return Object.assign({}, state, action.data.attribute);
    default:
        return state;
    }
}

function listenerStore (state, action) {
    switch (action.type) {
    case ADD_ATTRIBUTE_LISTENER:
        let model = `${action.data.device}/${action.data.attribute}`;
        let newState = Object.assign({}, state);
        newState[model] = action.data;
        return newState;
    case REMOVE_ATTRIBUTE_LISTENER:
        newState = Object.assign({}, state);
        delete newState[action.data.model];
        return newState;
    default:
        return state;
    }
}


// Combining the stores 

let initialState = {
    devices: {},
    domains: {},
    families: {},
    domains: {},    
    properties: {},
    attributes: {},    
    attribute_values: {},
    attribute_configs: {},    
    members: {},
    listeners: {}
}


// This is probably not the way to do it...
export default function data (state=initialState, action) {
    
    const devices = deviceStore(state.devices, action),
          domains = domainStore(state.domains, action),
          families = familyStore(state.families, action),
          members = memberStore(state.members, action),
          attributes = attributeStore(state.attributes, action),
          attribute_values = attributeValueStore(state.attribute_values, action),
          attribute_configs = attributeConfigStore(state.attribute_configs, action),          
          properties = propertyStore(state.properties, action),
          listeners = listenerStore(state.listeners, action);
    
    return {devices, domains, families, members, properties, attributes,
            attribute_values, attribute_configs, listeners};
}

