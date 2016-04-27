import React from "react";
import {findDOMNode} from "react-dom";
import { connect } from 'react-redux'
import {Responsive} from "react-grid-layout";
import {WidthProvider} from "react-grid-layout";
import {DropTarget} from "react-dnd";

import {setDashboardLayout, setDashboardContent, setDashboardCardTitle,
        addDashboardCard, removeDashboardCard} from "./actions";
import Attributes from "./attribute";
import Trend from "./trend";


const WidthReactGridLayout = WidthProvider(Responsive);


var ContentEditable = React.createClass({
    render: function(){
        return <span
            onInput={this.emitChange} 
            onBlur={this.emitChange}
            contentEditable
            dangerouslySetInnerHTML={{__html: this.props.html}}/>;
    },
    shouldComponentUpdate: function(nextProps){
        return nextProps.html !== findDOMNode(this).innerHTML;
    },
    emitChange: function(){
        var html = findDOMNode(this).innerHTML;
        if (this.props.onChange && html !== this.lastHtml) {

            this.props.onChange({
                target: {
                    value: html
                }
            });
        }
        this.lastHtml = html;
    }
});


class _Card extends React.Component {

    cardClass = "list-card"

    onChangeTitle (event) {
        //this.setState({title: event.target.value})
        this.props.dispatch(setDashboardCardTitle(
            {[this.props.index]: event.target.value}));
    }
    
    onRemove () {
        this.props.dispatch(removeDashboardCard(this.props.index));
    }

    onRemoveAttribute (attr) {
        if (!this.props.editMode)
            return
        const index = this.props.content.indexOf(attr)
        const newContent = [...this.props.content.slice(0, index),
                            ...this.props.content.slice(index+1)]
        this.props.dispatch(
            setDashboardContent({[this.props.index]: newContent}))
    }

    onInsertAttribute(model, index) {
        const newContent = [...this.props.content.slice(0, index),
                            model,
                            ...this.props.content.slice(index)]
        this.props.dispatch(
            setDashboardContent({[this.props.index]: newContent}))
    }
    
    getContent() {
        if (this.props.cardType == "TREND")
            return <Trend listeners={this.props.content || []} editMode={this.props.editMode}/>
        return <Attributes listeners={this.props.content || []} editMode={this.props.editMode}
                      onRemoveAttribute={this.onRemoveAttribute.bind(this)}
                      onInsertAttribute={this.onInsertAttribute.bind(this)}/>
    }

    getTitle () {
        if (this.props.editMode)
            return <ContentEditable html={this.props.title}
                                    onChange={this.onChangeTitle.bind(this)}/>
        return <span>{this.props.title}</span>
    }

    getClasses () {
        return "card " + this.props.cardType.toLowerCase() + (this.props.isOver? " over" : "")
    }
    
    render() {
        return this.props.connectDropTarget(
            <table className={this.getClasses()}>
                <thead>
                <tr>
                <th>
                <div className="card-index" style={{display: this.props.editMode? null : "none"}}>
                      {this.props.index}</div>
                {this.getTitle()}
                <button className="remove-card"
                        style={{display: this.props.editMode? null : "none"}}
                        onClick={this.onRemove.bind(this)}>
                    x
            </button>

                </th>
                </tr>
                </thead>
                <tbody>
                <tr><td>
                
                <div className="content">
                    {this.getContent()}
                </div>
            </td></tr>
            </tbody>                
            </table>);
    }
}


const cardTarget = {
    canDrop(props, monitor) {
        return true;
    },
    drop(props, monitor, component) {
        // user is dropping an attribute from the tree on the card
        // let's add the attribute to the content
        if (monitor.didDrop())
            return
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



class TangoDashboard extends React.Component {

    onLayoutChange (layout) {
        this.props.dispatch(setDashboardLayout(layout))
    }

    onAddCard (cardType) {
        this.props.dispatch(addDashboardCard(cardType));
    }

    render() {
        console.log("render dashboard");
        const cards = this.props.layout.map(
            l => {
                return (<div key={l.i} _grid={l}>
                        <Card index={l.i} cardType={this.props.cardType[l.i]}
                              title={this.props.cardTitle[l.i] || "(Title here)"}
                              content={this.props.content[l.i]}
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
                <button className="add-card" title="Add attribute card"
                        style={{display: this.props.editMode? null : "none"}}
                        onClick={this.onAddCard.bind(this, "LIST")}>
                A
                </button>

                <button className="add-trend" title="Add trend card"
                        style={{display: this.props.editMode? null : "none"}}
                        onClick={this.onAddCard.bind(this, "TREND")}>
                T
                </button>
            </div>
        );
    }
}


const mapStateToProps = (state) => {
    return {
        layout: state.data.dashboardLayout,
        content: state.data.dashboardContent,
        cardType: state.data.dashboardCardType,
        cardTitle: state.data.dashboardCardTitle
    }
}


export default connect(mapStateToProps)(TangoDashboard);
