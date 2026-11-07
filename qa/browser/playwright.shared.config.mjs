import base from './playwright.config.mjs';
export default {...base,testMatch:'atelier.spec.mjs',use:{...base.use,trace:'off'},workers:1,retries:0,outputDir:'shared-artifacts',reporter:[['list'],['html',{outputFolder:'shared-report',open:'never'}]]};
