import{j as e}from"./jsx-runtime-DX1rVzdN.js";import{r as p}from"./iframe-Bi2tD4Oz.js";import{M as l,a as c}from"./components-DUj7tQxJ.js";import"./preload-helper-C1FmrZbK.js";const L={title:"Components/Modal",component:l,argTypes:{isOpen:{control:"boolean"},title:{control:"text"},size:{control:"select",options:["sm","md","lg","xl","full"]}}},t={render:r=>{const[s,n]=p.useState(!1);return e.jsxs(e.Fragment,{children:[e.jsx(c,{onClick:()=>n(!0),children:"Open Modal"}),e.jsx(l,{...r,isOpen:s,onClose:()=>n(!1),children:e.jsx("p",{children:"Modal content goes here."})})]})},args:{title:"Example Modal"}},o={render:r=>{const[s,n]=p.useState(!1);return e.jsxs(e.Fragment,{children:[e.jsx(c,{onClick:()=>n(!0),children:"Open Small Modal"}),e.jsx(l,{...r,isOpen:s,onClose:()=>n(!1),children:e.jsx("p",{children:"Small modal content."})})]})},args:{title:"Small Modal",size:"sm"}},a={render:r=>{const[s,n]=p.useState(!1);return e.jsxs(e.Fragment,{children:[e.jsx(c,{onClick:()=>n(!0),children:"Open Large Modal"}),e.jsx(l,{...r,isOpen:s,onClose:()=>n(!1),children:e.jsx("p",{children:"Large modal content with plenty of space."})})]})},args:{title:"Large Modal",size:"lg"}};var d,i,m;t.parameters={...t.parameters,docs:{...(d=t.parameters)==null?void 0:d.docs,source:{originalSource:`{
  render: args => {
    const [open, setOpen] = useState(false);
    return <>\r
        <Button onClick={() => setOpen(true)}>Open Modal</Button>\r
        <Modal {...args} isOpen={open} onClose={() => setOpen(false)}>\r
          <p>Modal content goes here.</p>\r
        </Modal>\r
      </>;
  },
  args: {
    title: "Example Modal"
  }
}`,...(m=(i=t.parameters)==null?void 0:i.docs)==null?void 0:m.source}}};var u,g,O;o.parameters={...o.parameters,docs:{...(u=o.parameters)==null?void 0:u.docs,source:{originalSource:`{
  render: args => {
    const [open, setOpen] = useState(false);
    return <>\r
        <Button onClick={() => setOpen(true)}>Open Small Modal</Button>\r
        <Modal {...args} isOpen={open} onClose={() => setOpen(false)}>\r
          <p>Small modal content.</p>\r
        </Modal>\r
      </>;
  },
  args: {
    title: "Small Modal",
    size: "sm"
  }
}`,...(O=(g=o.parameters)==null?void 0:g.docs)==null?void 0:O.source}}};var M,f,x;a.parameters={...a.parameters,docs:{...(M=a.parameters)==null?void 0:M.docs,source:{originalSource:`{
  render: args => {
    const [open, setOpen] = useState(false);
    return <>\r
        <Button onClick={() => setOpen(true)}>Open Large Modal</Button>\r
        <Modal {...args} isOpen={open} onClose={() => setOpen(false)}>\r
          <p>Large modal content with plenty of space.</p>\r
        </Modal>\r
      </>;
  },
  args: {
    title: "Large Modal",
    size: "lg"
  }
}`,...(x=(f=a.parameters)==null?void 0:f.docs)==null?void 0:x.source}}};const B=["Default","Small","Large"];export{t as Default,a as Large,o as Small,B as __namedExportsOrder,L as default};
