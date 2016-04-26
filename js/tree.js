import React, { Component, PropTypes } from 'react'
import { connect } from 'react-redux'
import {DragSource} from 'react-dnd';

import { fetchDomain, fetchFamily, fetchMember, fetchAttribute,
         addAttributeListener } from './actions'


const attributeSource = {
    beginDrag(props) {
        console.log("beginDrag", props)        
        // return {
        //     device: props.device,
        //     attribute: props.name
        // };
        return {model: `${props.device}/${props.name}`};
    }
};


function collect(connect, monitor) {
    return {
        connectDragSource: connect.dragSource(),
        isDragging: monitor.isDragging()
    };
}


const propTypes = {
    // Injected by React DnD:
    isDragging: PropTypes.bool.isRequired,
    connectDragSource: PropTypes.func.isRequired
};


class TreeNode extends Component {

    constructor (props) {
        super(props);
        this.state = {open: false};
    }

    onClick() {
        this.setState({open: !this.state.open});
        if (this.props.children.length == 0)
            this.fetchChildren();
    }

    fetchChildren() {
    }

    getClass () {
        return "";
    }
    
    render () {
        var children;
        if (this.state.open)
            children = this.getChildren();
        return (
                <li>
                <span className={(this.state.open? "open" : "closed") + " " + this.getClass()}
                      onClick={this.onClick.bind(this)}>{this.props.name}</span>
                    
                <ul>
                    { children }
                </ul>
            </li>
        );
    }
}


class DomainTreeNode extends TreeNode {

    children: "families"
    
    fetchChildren() {
        this.props.dispatch(fetchFamily(this.props.name, "*"));
    }

    getClass() {
        return "domain"
    }
    
    getChildren() {
        return this.props.children.map((name) => {
            const family = this.props.store.families[name];
            return <FamilyTreeNode {...this.props} key={name} name={family.name}
                       domain={this.props.name}
                       children={family.members || []}
                />;
        });
    }
    
}

class FamilyTreeNode extends TreeNode {

    children: "members"

    fetchChildren() {
        this.props.dispatch(fetchMember(this.props.domain,
                                        this.props.name, "*"));
    }

    getClass() {
        return "family"
    }
    
    getChildren() {
        return this.props.children.map(path => {
            const member = this.props.store.members[path];
            return <MemberTreeNode {...this.props} key={path}
                       name={member.name} path={path} exported={member.exported}/>
        });
    }
}

class MemberTreeNode extends TreeNode {

    children: "properties"

    getDeviceName() {
        return `${this.props.domain}/${this.props.family}/${this.props.name}`;
    }
    
    getClass() {
        return "member " + (this.props.exported? "exported" : "unexported");
    }
    
    getChildren() {
        var children = [];
        return [<AttributesTreeNode {...this.props}
            key="attributes" path={this.props.path + "/attributes"}
            children={children || []}
        name="attributes" device={this.props.path}/>]
    }
}


class AttributesTreeNode extends TreeNode {

    fetchChildren() {
        this.props.dispatch(fetchAttribute(this.props.device));
    }

    getChildren() {
        let device = this.props.store.devices[this.props.device];
        if (device) {
            let children = device.attributes || [];
            return children.map(path => {
                let attribute = this.props.store.attributes[path];
                return <Attribute key={path} {...attribute}
                             device={this.props.device}
                             dispatch={this.props.dispatch}/>;
            });
        }
    }
}


class _Attribute extends Component {

    onClick () {
        this.props.dispatch(addAttributeListener(this.props.device,
                                                 this.props.name));
    }
    
    render () {
        const { isDragging, connectDragSource, text,
                datatype, dataformat } = this.props;
        const classes = `attribute type-${datatype.toLowerCase()} format-${dataformat.toLowerCase()}`;

        if (dataformat != "IMAGE")
            return connectDragSource(
                    <div className={classes} title={this.props.label + " type:" +
                                                    this.props.datatype + " unit:" +
                                                    this.props.unit + " desc:" +
                                                    this.props.description}
                       onClick={this.onClick.bind(this)}>
                          {this.props.name}
                       </div>);
        else
            return (<div className={classes} onClick={this.onClick.bind(this)}>
                        {this.props.name}
                    </div>);
            
    }
}

const Attribute = DragSource("ATTRIBUTE", attributeSource, collect)(_Attribute);


function getDomainPattern(pattern) {
    if (pattern.indexOf("/") != -1)
        return pattern.split("/")[0]
    return 
}


class Tree extends Component {

    componentWillMount(props) {
        this.props.dispatch(fetchDomain(this.props.pattern || "*"))
    }
    
    render() {
        var nodes = Object.keys(this.props.store.domains).map(
            name => {
                const domain = this.props.store.domains[name];
                return <DomainTreeNode {...this.props} className="tree"
                           key={domain.name} name={domain.name}
                           children={domain.families || []}/>
            }
        )
        return (<div className="tree">
                 <ul> { nodes } </ul>
                </div>);
    }
}


function select (state) {
    return {
        store: state.data
    }
}

export default connect(select)(Tree);
