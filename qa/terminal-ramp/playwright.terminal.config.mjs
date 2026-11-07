import base from './playwright.config.mjs';
export default {...base,testMatch:/(?:atelier-combined-r17|atelier-terminal)\.spec\.mjs/,use:{...base.use,trace:'off'},workers:1,retries:0,outputDir:'terminal-artifacts',reporter:[['list'],['html',{outputFolder:'terminal-report',open:'never'}]]};
