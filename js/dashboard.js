import React from "react";
import { connect } from 'react-redux'
import ReactGridLayout from "react-grid-layout";
import {WidthProvider} from "react-grid-layout";
import {DropTarget} from "react-dnd";

import {setDashboardLayout, setDashboardContent,
        addDashboardCard, removeDashboardCard} from "./actions";
import Attributes from "./attribute";

const WidthReactGridLayout = WidthProvider(ReactGridLayout);


class _Card extends React.Component {

    cardClass = "list-card"
    
    onRemove () {
        this.props.dispatch(removeDashboardCard(this.props.index));
    }

    onRemoveAttribute (attr) {
        const index = this.props.content.indexOf(attr)
        const newContent = [...this.props.content.slice(0, index),
                            ...this.props.content.slice(index+1)]
        this.props.dispatch(setDashboardContent({[this.props.index]: newContent}))
    }
    
    getContent() {
        return <Attributes listeners={this.props.content || []}
                           onRemoveAttribute={this.onRemoveAttribute.bind(this)}/>
    }
    
    render() {
        return this.props.connectDropTarget(
            <div className={"card" + " " + this.cardClass + (this.props.isOver? " over" : "")}>
                <button className="remove-card"
                        style={{display: this.props.editMode? null : "none"}}
                        onClick={this.onRemove.bind(this)}>
                    x
                </button>
                <div className="content">
                {this.getContent()}
                </div>
            </div>);
    }
}


const cardTarget = {
    canDrop(props, monitor) {
        return true;
    },
    drop(props, monitor, component) {
        // user is dropping an attribute from the tree on the card
        // let's add the attribute to the content
        let item = monitor.getItem();
        let content = [...(props.content || []), item.model];
        props.dispatch(setDashboardContent({[props.index]: content}));
    }
}


function collect(connect, monitor) {
    return {
        connectDropTarget: connect.dropTarget(),
        isOver: monitor.isOver()
    }
}


// A card that can accept dropped attributes
const Card = DropTarget("ATTRIBUTE", cardTarget, collect)(_Card);


class _PlotCard extends _Card {

    cardClass = "plot-card"
    
    getContent() {
        return <div>Hello</div>
    }
    
}


const PlotCard = DropTarget("ATTRIBUTE", cardTarget, collect)(_PlotCard);


class TangoDashboard extends React.Component {

    onLayoutChange (layout) {
        this.props.dispatch(setDashboardLayout(layout))
    }

    onAddCard () {
        this.props.dispatch(addDashboardCard());
    }

    onAddPlotCard() {
        this.props.dispatch(addDashboardCard("PLOT"))
    }
    
    render() {
        console.log("render dashboard");
        const cards = this.props.layout.map(
            l => {
                return (<div key={l.i} _grid={l}>
                        <Card index={l.i} content={this.props.content[l.i]}
                        editMode={this.props.editMode}
                        dispatch={this.props.dispatch}/>
                        </div>);
            });
        
        return (
            <div className="dashboard">
                <WidthReactGridLayout className="dashboard"
                        autoSize={true} rowHeight={30}
                        isDraggable={this.props.editMode} isResizable={this.props.editMode}
                        onResizeStop={this.onLayoutChange.bind(this)}
                        onDragStop={this.onLayoutChange.bind(this)}>
                    {cards}
                </WidthReactGridLayout>
                <button className="add-card" style={{display: this.props.editMode? null : "none"}}
                        onClick={this.onAddCard.bind(this)}>
                +
                </button>

                <button className="add-plot-card" style={{display: this.props.editMode? null : "none"}}
                        onClick={this.onAddPlotCard.bind(this)}>
                +
                </button>
            </div>
        );
    }
}


const mapStateToProps = (state) => {
    return {
        layout: state.data.dashboardLayout,
        content: state.data.dashboardContent,
    }
}


export default connect(mapStateToProps)(TangoDashboard);
