// Copy beside existing watch-browser-qa/playwright.config.mjs.
import base from './playwright.config.mjs';
export default {...base,testMatch:'material-review.spec.mjs',timeout:600000,workers:1,retries:0,outputDir:'material-artifacts',reporter:[['list'],['html',{outputFolder:'material-report',open:'never'}]]};
