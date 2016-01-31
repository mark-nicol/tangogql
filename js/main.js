import React from "react";
import { render } from "react-dom";
import { createStore, applyMiddleware, combineReducers } from 'redux';
import { normalize, Schema, arrayOf } from 'normalizr';
import { Provider } from 'react-redux'
import createLogger from 'redux-logger';
import thunkMiddleware from 'redux-thunk'
import Lokka from "lokka";
import Transport from "lokka-transport-http"

import data from "./store.js";
import AttributeListenerList from "./attribute";
import Tree from "./tree"
import {fetchDomain, fetchFamily, fetchMember} from "./store";
import {receiveChange, receiveConfig,
        ADD_ATTRIBUTE_LISTENER, REMOVE_ATTRIBUTE_LISTENER} from "./actions";


// redux store

const logger = createLogger();

const createStoreWithMiddleware = applyMiddleware(
    thunkMiddleware // lets us dispatch() functions
    , logger
)(createStore)

function lastAction(state = null, action) {
    return action;
}

const rootReducer = combineReducers({
    data,
    lastAction
});

let store = createStoreWithMiddleware(rootReducer);


// tree view
let treeContainer = document.getElementById("tree");
render(
    <Provider store={store}>
        <Tree pattern="*"/>
    </Provider>,
    treeContainer
);

// attribute listener view
let mainContainer = document.getElementById("main");
render(
    <Provider store={store}>
        <AttributeListenerList/>
    </Provider>,
    mainContainer
);


/* hacking a websocket in "on top" of the redux store... */

var ws = new WebSocket("ws://" + window.location.host + "/socket");


ws.addEventListener("message", msg => {
    console.log(msg.data)
    var event = JSON.parse(msg.data);
    store.dispatch(event);
});


ws.addEventListener("open", () => {
    console.log("Websocket open!")
});

ws.addEventListener("error", (e) => {
    console.log("Websocket error!", e)
});


function wsListener (a) {
    let {session, lastAction} = store.getState();
    if (!lastAction)
        return
    switch (lastAction.type) {
    case ADD_ATTRIBUTE_LISTENER:
        let model = `${lastAction.data.device}/${lastAction.data.attribute}`;
        ws.send(JSON.stringify({"type": "SUBSCRIBE",
                                "models": [model]}));
        break;
    case REMOVE_ATTRIBUTE_LISTENER:
        ws.send(JSON.stringify({"type": "UNSUBSCRIBE",
                                "models": [lastAction.data.model]}));
        break;
    }
}

store.subscribe(wsListener);
