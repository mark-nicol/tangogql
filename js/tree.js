import React, { Component, PropTypes } from 'react'
import { connect } from 'react-redux'

import { fetchDomain, fetchFamily, fetchMember, fetchAttribute,
         addAttributeListener } from './actions'



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
    
    render () {
        var children;
        if (this.state.open)
            children = this.getChildren();
        return (
            <li>
                <div onClick={this.onClick.bind(this)}>{this.props.name}</div>
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
    
    getChildren() {
        return this.props.children.map(path => {
            const member = this.props.store.members[path];
            return <MemberTreeNode {...this.props} key={path} name={member.name} path={path}/>
        });
    }
}

class MemberTreeNode extends TreeNode {

    children: "properties"

    getDeviceName() {
        return `${this.props.domain}/${this.props.family}/${this.props.name}`;
    }
    
    fetchChildren() {
        
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
        console.log("AttribuitesTreeNode.fetchDChildren");
        this.props.dispatch(fetchAttribute(this.props.device));
    }

    getChildren() {
        let device = this.props.store.devices[this.props.device];
        if (device) {
            let children = device.attributes || [];
            return children.map(path => {
                let attribute = this.props.store.attributes[path];
                return <Attribute key={path} name={attribute.name}
                             device={this.props.device}
                             dispatch={this.props.dispatch}/>;
            });
        }
    }
}


class Attribute extends Component {

    onClick () {
        this.props.dispatch(addAttributeListener(this.props.device,
                                                 this.props.name));
    }
    
    render () {
        return <div onClick={this.onClick.bind(this)}>{this.props.name}</div>;
    }
}


class Tree extends Component {

    componentWillMount(props) {
        this.props.dispatch(fetchDomain(this.props.pattern || "*"))
    }
    
    render() {
        var nodes = Object.keys(this.props.store.domains).map(
            name => {
                const domain = this.props.store.domains[name];
                return <DomainTreeNode {...this.props}
                           key={domain.name} name={domain.name}
                           children={domain.families || []}/>
            }
        )
        return (<ul> { nodes } </ul>);
    }
}


function select (state) {
    return {
        store: state.data
    }
}

export default connect(select)(Tree);
