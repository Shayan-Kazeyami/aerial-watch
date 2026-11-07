import base from './playwright.config.mjs';
export default {...base,use:{...base.use,trace:'off'},testMatch:'independent-camera.spec.mjs',timeout:360000,workers:1,retries:0,outputDir:'camera-diagnostic-artifacts'};
