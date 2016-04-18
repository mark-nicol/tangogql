import React from "react";
import { render } from "react-dom";
import { createStore, applyMiddleware, combineReducers } from 'redux';
import { normalize, Schema, arrayOf } from 'normalizr';
import { Provider } from 'react-redux'
import createLogger from 'redux-logger';
import thunkMiddleware from 'redux-thunk'
import Lokka from "lokka";
import Transport from "lokka-transport-http"
import HTML5Backend from 'react-dnd-html5-backend';
import { DragDropContext } from 'react-dnd';

import data from "./store.js";
import AttributeListenerList from "./attribute";
import Tree from "./tree"
import {fetchDomain, fetchFamily, fetchMember} from "./store";
import {receiveChange, receiveConfig, setDashboardLayout, setDashboardContent,
        ADD_ATTRIBUTE_LISTENER, REMOVE_ATTRIBUTE_LISTENER} from "./actions";
import TangoDashboard from "./dashboard";
import {loadStateFromHash, setHashFromState, debounce} from "./util";


// redux store

const logger = createLogger();

const createStoreWithMiddleware = applyMiddleware(
    thunkMiddleware // lets us dispatch() functions
    , logger // logs all actions to console for debugging
)(createStore)

function lastAction(state = null, action) {
    return action;
}

const rootReducer = combineReducers({
    data,
    lastAction  // used by the websocket hack below
});

let store = createStoreWithMiddleware(rootReducer);


// GUI

let mainContainer = document.getElementById("container");

class _App extends React.Component {

    render() {
        return (
                <section id="inner" className="main hbox space-between">
                <nav id="tree">
                <Tree pattern="*" store={this.props.store}/>
                </nav>
                <article id="main">
                <TangoDashboard width={500}/>
                </article>
                </section>
        );
    }
    
}

const App = DragDropContext(HTML5Backend)(_App);1

render(
        <Provider store={store}>
        <App/>
        </Provider>,
    mainContainer
)


/* hacking a websocket in "on top" of the redux store... 
This might be better done through middleware?*/

var ws = new WebSocket("ws://" + window.location.host + "/socket", "json");


ws.addEventListener("message", msg => {
    var data = JSON.parse(msg.data);
    console.log(data);
    data.events.forEach(e => store.dispatch(e));
});


ws.addEventListener("open", () => {
    console.log("Websocket open!")
    setupHashHandling();
});


ws.addEventListener("error", (e) => {
    console.log("Websocket error!", e)
});


function wsListener () {
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


function setupHashHandling() {

    /* 
       Setup browser URL handling. 

       The layout (all the boxes' positions and dimensions) and content (which attributes go in which box)
       are stored as a JSON string in the URL "hash". This means that it's easy to save a dashboard as it's
       all encoded inside the URL - just make a bookmark.

       On the other hand, it looks like URL:s should be capped at ~2000 characters or they might not work 
       in all browsers. Not sure how to handle this, or if it will even be a problem. JSON is a pretty 
       wasteful protocol for storing information so we can easily optimize this if needed.

       Also, this code is pretty simplistic and probably does not handle every case.
    */
    
    let currentHash;

    function dispatchFromHash() {
        if (document.location.hash == currentHash)  // avoid circular behavior
            return
        else
            currentHash = document.location.hash
        const hashData = loadStateFromHash()
        store.dispatch(setDashboardLayout(hashData.layout));
        store.dispatch(setDashboardContent(hashData.content));
    }

    // if the URL changes, update the dashboard    
    window.addEventListener("hashchange", function () {
        dispatchFromHash();
    })

    // conversely, update the URL if the dashboard changes
    store.subscribe(debounce(function () {
        setHashFromState(store.getState());
        currentHash = document.location.hash;
    }, 100));

    if (document.location.hash.length > 1) {
        dispatchFromHash();
    }
    
}
