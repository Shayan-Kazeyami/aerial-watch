import base from './playwright.config.mjs';
export default {...base,testMatch:/(?:atelier-combined-r18|atelier-return-material)\.spec\.mjs/,use:{...base.use,trace:'off'},workers:1,retries:0,outputDir:'return-material-artifacts',reporter:[['list'],['html',{outputFolder:'return-material-report',open:'never'}]]};
