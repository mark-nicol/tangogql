/* redux actions */

import Lokka from "lokka";
import Transport from "lokka-transport-http"
import { normalize, Schema, arrayOf } from 'normalizr';


export const RECEIVE = "RECEIVE";
export const ADD_ATTRIBUTE_LISTENER = "ADD_ATTRIBUTE_LISTENER";
export const REMOVE_ATTRIBUTE_LISTENER = "REMOVE_ATTRIBUTE_LISTENER";
export const CHANGE = "CHANGE";
export const CONFIG = "CONFIG";
export const SET_DASHBOARD_LAYOUT = "SET_DASHBOARD_LAYOUT"
export const SET_DASHBOARD_CONTENT = "SET_DASHBOARD_CONTENT"
export const ADD_DASHBOARD_CARD = "ADD_DASHBOARD_CARD"
export const REMOVE_DASHBOARD_CARD = "REMOVE_DASHBOARD_CARD"
export const SET_DASHBOARD_CARD_TYPE = "SET_DASHBOARD_CARD_TYPE"
export const SET_DASHBOARD_CARD_TITLE = "SET_DASHBOARD_CARD_TITLE"


export function receiveData(data) {
    return { type: RECEIVE, data }
}

export function receiveChange(data) {
    return { type: CHANGE, data }
}

export function receiveConfig(data) {
    return { type: CONFIG, data }
}

export function addAttributeListener(model) {
    return { type: ADD_ATTRIBUTE_LISTENER,
             data: {model} } 
}

export function removeAttributeListener(model) {
    return { type: REMOVE_ATTRIBUTE_LISTENER,
             data: {model} } 
}

export function setDashboardLayout(layout) {
    return {type: SET_DASHBOARD_LAYOUT, layout}
}

// update the content (attributes) of one or more cards
// the argument should be an object keyed by card index,
// and containing lists of attributes
export function setDashboardContent(content) {
    return (dispatch, getState) => {
        const state = getState();
        Object.keys(content).forEach(key => {
            let items = content[key];
            const oldItems = state.data.dashboardContent[key] || [];
            // add listeners for the attributes (this is idempotent)
            items.forEach(model => {
                dispatch(addAttributeListener(model));
            });
            // check if any removed attributes are still used,
            // otherwise unsubscribe them
            oldItems.forEach(model => {
                if (items.indexOf(model) == -1) {
                    if (!checkForAttributeInDashboard(state, model, key)) {
                        dispatch(removeAttributeListener(model));
                    }
                }
            });
        });
        dispatch({type: SET_DASHBOARD_CONTENT, content});
    };
}


// produce a new, unique card index
function makeCardIndex(state) {
    let i;
    if (state.data.dashboardLayout.length > 0) {
        let tmpState = [...state.data.dashboardLayout];
        tmpState.sort((c1, c2) => parseInt(c1.i) > parseInt(c2.i));
        let lastCard = tmpState[tmpState.length-1];
        i = parseInt(lastCard.i) + 1;
    } else {
        i = 0;
    }
    return i.toString();
}

export function addDashboardCard(cardType) {
    return (dispatch, getState) => {
        let index = makeCardIndex(getState());
        dispatch({type: ADD_DASHBOARD_CARD, index, cardType})
    }
}


// return whether an attribute is used somewhere else in the dashboard
function checkForAttributeInDashboard(state, attr, skipIndex) {
    const content = state.data.dashboardContent;
    for (let index of Object.keys(content)) {
        if (index != skipIndex && content[index].indexOf(attr) !== -1)
            return true;
    }
    return false;
}

export function removeDashboardCard(index) {
    return function (dispatch, getState) {
        const state = getState();
        const content = state.data.dashboardContent[index];
        content.forEach(model => {
            if (!checkForAttributeInDashboard(state, model, index))
                dispatch(removeAttributeListener(model));
        });
        dispatch({type: REMOVE_DASHBOARD_CARD, index});
    }
}

export function setDashboardCardType(cardTypes) {
    return {type: SET_DASHBOARD_CARD_TYPE, cardTypes};
}

export function setDashboardCardTitle(titles) {
    return {type: SET_DASHBOARD_CARD_TITLE, titles};
}


// normalizr schema definitions

const getName = entity => entity.name,
      getPropertyId = p => `${p.device}/${p.name}`,
      getAttributeId = a => `${a.device}/${a.name}`,
      getDomainId = d => d.name,
      getFamilyId = f => `${f.domain}/${f.name}`,
      getMemberId = m => `${m.domain}/${m.family}/${m.name}`;

const device = new Schema("device", {idAttribute: getName}),
      property = new Schema("property", {idAttribute: getPropertyId}),
      attribute = new Schema("attribute", {idAttribute: getAttributeId}),
      domain = new Schema("domain", {idAttribute: getDomainId}),
      family = new Schema("family", {idAttribute: getFamilyId}),
      member = new Schema("member", {idAttribute: getMemberId});

device.define({
    properties: arrayOf(property),
    attributes: arrayOf(attribute)
})
domain.define({families: arrayOf(family)});
family.define({members: arrayOf(member)});
member.define({
    properties: arrayOf(property),
    attributes: arrayOf(attribute)
})


const client = new Lokka({transport: new Transport('/db')});


// a helper to dispatch actions for whatever data we got
function dataDispatcher(dispatch, result) {
    // console.log("result", result);                    
    const data = normalize(result, {
        devices: arrayOf(device),
        properties: arrayOf(property),
        attributes: arrayOf(attribute), 
        domains: arrayOf(domain),
        families: arrayOf(family),
        members: arrayOf(member),
    });
    // console.log("normalized", data);
    dispatch(receiveData(data.entities));
}


export function fetchDomain(pattern) {

    return dispatch => {

        var q = `{
    domains(pattern: "${pattern}") {
        name
    }
}`;
        
        client.query(q)
            .then(result => {
                dataDispatcher(dispatch, result);
            }, error => {console.log("error", error)});

    }
    
}


export function fetchFamily(domain, pattern) {

    return dispatch => {
        //dispatch(requestDevices("blabla"))
        var q = `{
        domains(pattern: "${domain}") {
            name
            families(pattern: "${pattern}") {
               domain
               name
            }
        }

    }`;
        
        client.query(q)
            .then(result => {
                dataDispatcher(dispatch, result);
            }, error => {console.log("error", error)});

    }
    
}


export function fetchMember(domain, family, pattern) {

    return dispatch => {
        //dispatch(requestDevices("blabla"))
        var q = `{
        families(domain: "${domain}", pattern: "${family}") {
            domain
            name
            members(pattern: "${pattern}") { 
               domain
               family
               name
               exported
            }
        }
    }`;
        
        client.query(q)
            .then(result => {
                dataDispatcher(dispatch, result);
            }, error => {console.log("error", error)});

    }
    
}


export function fetchAttribute(device) {

    return dispatch => {
        //dispatch(requestDevices("blabla"))
        var q = `{
        devices(pattern: "${device}") {
            name
            attributes { 
               device
               name
               label
               unit
               description
               datatype
               dataformat
            }
        }
    }`;
        
        client.query(q)
            .then(result => {
                dataDispatcher(dispatch, result);
            }, error => {console.log("error", error)});

    }
    
}
