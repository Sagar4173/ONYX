import{j as D}from"./jsx-runtime-DX1rVzdN.js";import{A as W}from"./components-DUj7tQxJ.js";import"./iframe-Bi2tD4Oz.js";import"./preload-helper-C1FmrZbK.js";const O={title:"Components/Alert",component:W,argTypes:{variant:{control:"select",options:["info","success","danger","warning"]},title:{control:"text"},children:{control:"text"}}},e={args:{children:"This is an informational message.",variant:"info"}},r={args:{children:"Operation completed successfully.",variant:"success",title:"Success"}},s={args:{children:"An error occurred while processing your request.",variant:"danger",title:"Error"}},n={args:{children:"Please review the configuration before proceeding.",variant:"warning",title:"Warning",onClose:()=>{}}},a={args:{children:"Alert with a custom icon.",icon:D.jsx("span",{children:"⚠"}),title:"Notice"}},o={args:{children:"Click the × button to dismiss this alert.",onClose:()=>alert("Dismissed!")}};var t,i,c;e.parameters={...e.parameters,docs:{...(t=e.parameters)==null?void 0:t.docs,source:{originalSource:`{
  args: {
    children: "This is an informational message.",
    variant: "info"
  }
}`,...(c=(i=e.parameters)==null?void 0:i.docs)==null?void 0:c.source}}};var l,d,m;r.parameters={...r.parameters,docs:{...(l=r.parameters)==null?void 0:l.docs,source:{originalSource:`{
  args: {
    children: "Operation completed successfully.",
    variant: "success",
    title: "Success"
  }
}`,...(m=(d=r.parameters)==null?void 0:d.docs)==null?void 0:m.source}}};var p,u,g;s.parameters={...s.parameters,docs:{...(p=s.parameters)==null?void 0:p.docs,source:{originalSource:`{
  args: {
    children: "An error occurred while processing your request.",
    variant: "danger",
    title: "Error"
  }
}`,...(g=(u=s.parameters)==null?void 0:u.docs)==null?void 0:g.source}}};var h,f,v;n.parameters={...n.parameters,docs:{...(h=n.parameters)==null?void 0:h.docs,source:{originalSource:`{
  args: {
    children: "Please review the configuration before proceeding.",
    variant: "warning",
    title: "Warning",
    onClose: () => {}
  }
}`,...(v=(f=n.parameters)==null?void 0:f.docs)==null?void 0:v.source}}};var S,w,A;a.parameters={...a.parameters,docs:{...(S=a.parameters)==null?void 0:S.docs,source:{originalSource:`{
  args: {
    children: "Alert with a custom icon.",
    icon: <span>⚠</span>,
    title: "Notice"
  }
}`,...(A=(w=a.parameters)==null?void 0:w.docs)==null?void 0:A.source}}};var x,C,b;o.parameters={...o.parameters,docs:{...(x=o.parameters)==null?void 0:x.docs,source:{originalSource:`{
  args: {
    children: "Click the × button to dismiss this alert.",
    onClose: () => alert("Dismissed!")
  }
}`,...(b=(C=o.parameters)==null?void 0:C.docs)==null?void 0:b.source}}};const T=["Info","Success","Danger","Warning","WithIcon","Dismissible"];export{s as Danger,o as Dismissible,e as Info,r as Success,n as Warning,a as WithIcon,T as __namedExportsOrder,O as default};
