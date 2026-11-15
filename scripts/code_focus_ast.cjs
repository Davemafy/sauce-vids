"use strict";
// Source AST parsing in a bounded local subprocess. Never execute the code.
const fs=require("fs");
const parser=require("@babel/parser");
const request=JSON.parse(fs.readFileSync(0,"utf8"));
const source=request.source;
const line=request.line;
if(typeof source!=="string"||source.length>1000000||!Number.isInteger(line))throw Error("Invalid AST parse input");
const tree=parser.parse(source,{
  sourceType:"unambiguous",errorRecovery:false,
  plugins:["typescript","jsx","decorators-legacy","classProperties","topLevelAwait"]
});
const nodes=[];
function walk(node,inheritName){
 if(!node||typeof node!=="object"||!node.type)return;
 const kind=node.type;
 const name=node.id?.name||node.key?.name||inheritName||kind;
 if(["FunctionDeclaration","FunctionExpression","ArrowFunctionExpression",
     "ClassDeclaration","ClassExpression","ObjectMethod","ClassMethod","ClassPrivateMethod"].includes(kind)&&node.loc){
   const begin=node.loc.start.line,end=node.loc.end.line;
   if(begin<=line&&line<=end)nodes.push({
     type:kind,name,begin,end,depth:end-begin
   });
 }
 for(const [k,v] of Object.entries(node)){
   if(k==="loc"||k==="tokens"||k==="comments"||k==="extra")continue;
   const localName=kind==="VariableDeclarator"&&node.id?.name?node.id.name:name;
   if(Array.isArray(v)){for(const child of v)if(child?.type)walk(child,localName);}
   else if(v?.type)walk(v,localName);
 }
}
walk(tree.program,null);
nodes.sort((a,b)=>a.depth-b.depth);
process.stdout.write(JSON.stringify(nodes[0]||null));
