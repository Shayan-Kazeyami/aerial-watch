// Copy beside the existing smoke config in watch-browser-qa.
import base from './playwright.config.mjs';
export default {...base,use:{...base.use,trace:'off'},testMatch:'resilience.spec.mjs',timeout:600000,workers:1,retries:0,outputDir:'resilience-artifacts',reporter:[['list'],['html',{outputFolder:'resilience-report',open:'never'}]]};
