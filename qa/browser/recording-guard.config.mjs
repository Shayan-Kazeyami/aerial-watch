import base from './playwright.config.mjs';
export default {...base,testMatch:'recording-guard.spec.mjs',workers:1,retries:0,timeout:720000,outputDir:'recording-guard-artifacts',reporter:[['list'],['html',{outputFolder:'recording-guard-report',open:'never'}]],use:{...base.use,actionTimeout:45000,trace:'off'}};
