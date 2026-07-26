import{I as P}from"./components-DUj7tQxJ.js";import"./jsx-runtime-DX1rVzdN.js";import"./iframe-Bi2tD4Oz.js";import"./preload-helper-C1FmrZbK.js";const I={title:"Components/Input",component:P,argTypes:{label:{control:"text"},placeholder:{control:"text"},error:{control:"text"},hint:{control:"text"},disabled:{control:"boolean"},readOnly:{control:"boolean"},type:{control:"select",options:["text","email","password","number","search"]}}},e={args:{placeholder:"Enter text..."}},a={args:{label:"Username",placeholder:"Enter your username"}},r={args:{label:"Email",defaultValue:"invalid",error:"Please enter a valid email address"}},s={args:{label:"Password",type:"password",hint:"Must be at least 8 characters"}},t={args:{label:"Disabled",defaultValue:"Cannot edit",disabled:!0}},o={args:{label:"Read Only",defaultValue:"Pre-filled value",readOnly:!0}};var l,n,d;e.parameters={...e.parameters,docs:{...(l=e.parameters)==null?void 0:l.docs,source:{originalSource:`{
  args: {
    placeholder: "Enter text..."
  }
}`,...(d=(n=e.parameters)==null?void 0:n.docs)==null?void 0:d.source}}};var c,i,u;a.parameters={...a.parameters,docs:{...(c=a.parameters)==null?void 0:c.docs,source:{originalSource:`{
  args: {
    label: "Username",
    placeholder: "Enter your username"
  }
}`,...(u=(i=a.parameters)==null?void 0:i.docs)==null?void 0:u.source}}};var p,m,b;r.parameters={...r.parameters,docs:{...(p=r.parameters)==null?void 0:p.docs,source:{originalSource:`{
  args: {
    label: "Email",
    defaultValue: "invalid",
    error: "Please enter a valid email address"
  }
}`,...(b=(m=r.parameters)==null?void 0:m.docs)==null?void 0:b.source}}};var g,h,y;s.parameters={...s.parameters,docs:{...(g=s.parameters)==null?void 0:g.docs,source:{originalSource:`{
  args: {
    label: "Password",
    type: "password",
    hint: "Must be at least 8 characters"
  }
}`,...(y=(h=s.parameters)==null?void 0:h.docs)==null?void 0:y.source}}};var f,x,E;t.parameters={...t.parameters,docs:{...(f=t.parameters)==null?void 0:f.docs,source:{originalSource:`{
  args: {
    label: "Disabled",
    defaultValue: "Cannot edit",
    disabled: true
  }
}`,...(E=(x=t.parameters)==null?void 0:x.docs)==null?void 0:E.source}}};var O,v,D;o.parameters={...o.parameters,docs:{...(O=o.parameters)==null?void 0:O.docs,source:{originalSource:`{
  args: {
    label: "Read Only",
    defaultValue: "Pre-filled value",
    readOnly: true
  }
}`,...(D=(v=o.parameters)==null?void 0:v.docs)==null?void 0:D.source}}};const R=["Default","WithLabel","WithError","WithHint","Disabled","ReadOnly"];export{e as Default,t as Disabled,o as ReadOnly,r as WithError,s as WithHint,a as WithLabel,R as __namedExportsOrder,I as default};
