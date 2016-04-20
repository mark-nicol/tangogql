/* redux store */

import {RECEIVE, CHANGE, CONFIG, ADD_ATTRIBUTE_LISTENER,
        REMOVE_ATTRIBUTE_LISTENER,
        SET_DASHBOARD_LAYOUT, ADD_DASHBOARD_CARD, REMOVE_DASHBOARD_CARD,
        SET_DASHBOARD_CONTENT} from "./actions";


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


function dashboardLayoutStore (state, action) {
    switch (action.type) {
    case SET_DASHBOARD_LAYOUT:
        return action.layout;
    case ADD_DASHBOARD_CARD:
        let i;
        if (state.length > 0) {
            let tmpState = [...state];
            tmpState.sort((c1, c2) => parseInt(c1.i) > parseInt(c2.i));
            let lastCard = tmpState[tmpState.length-1];
            i = parseInt(lastCard.i) + 1;
        } else {
            i = 0;
        }
        let newCard;
        if (action.cardType == "PLOT")
            newCard = {i: i.toString(), x: 0, y: 100, w: 5, h: 3};
        else
            newCard = {i: i.toString(), x: 0, y: 100, w: 3, h: 2};
        return [...state, newCard];
    case REMOVE_DASHBOARD_CARD:
        let index = state.indexOf(state.find(card => card.i == action.index))
        return [...state.slice(0, index), ...state.slice(index+1)];
    }
    return state;
}


function dashboardContentStore (state, action) {
    switch (action.type) {
    case SET_DASHBOARD_CONTENT:
        return Object.assign({}, state, action.content);
    case REMOVE_DASHBOARD_CARD:
        // TODO: implement this!
        break;
    case REMOVE_ATTRIBUTE_LISTENER:
        
    }
    return state;
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
    listeners: {},
    dashboardLayout: [
        {i: "0", x: 0, y: 0, w: 4, h: 4},
    ],
    dashboardContent: {}
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
          listeners = listenerStore(state.listeners, action),
          dashboardLayout = dashboardLayoutStore(state.dashboardLayout, action),
          dashboardContent = dashboardContentStore(state.dashboardContent, action);
    
    return {devices, domains, families, members, properties, attributes,
            attribute_values, attribute_configs, listeners,
            dashboardLayout, dashboardContent};
}

