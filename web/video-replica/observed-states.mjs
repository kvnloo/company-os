// Human-checked source samples, not live telemetry. Timing is sample-and-hold:
// a changed value occurred AFTER the prior visible observation, not necessarily at t.
// Native crop [110,648,790,673] mapped through tracks.json components.lanes.matrix;
// review receipt: motion-analysis/lane-summary-sheet.png. Gaps remain unobserved.
export const summaryObservations=[
 {t:0,frame:0,values:['18','16','9,847','0','3']},
 {t:1,frame:60,values:['19','17','9,847','0','4']},
 {t:4,frame:240,values:['19','18','9,336','0','4']},
 {t:5.5,frame:330,values:['19','18','10,828','0','4']},
 {t:6,frame:360,values:['19','18','10,875','0','4']},
 {t:6.5,frame:390,values:['19','19','10,375','0','4']},
 {t:7,frame:420,values:['19','20','10,169','0','4']},
 {t:8,frame:480,values:['19','21','10,351','0','4']},
 {t:8.5,frame:510,values:['19','21','10,504','0','4']},
 {t:9.5,frame:570,values:['19','21','10,396','0','4']},
 {t:10,frame:600,values:['19','21','9,507','0','4']},
 {t:11,frame:660,values:['19','22','9,531','0','4']},
 {t:11.5,frame:690,values:['19','27','9,766','0','4']},
 {t:12.5,frame:750,values:['19','26','9,581','0','5']},
 {t:13,frame:780,values:['19','25','9,487','0','5']},
 {t:14,frame:840,values:['19','25','9,326','0','5']},
 {t:14.5,frame:870,values:['19','25','9,191','0','5']}
];
export const laneOrders=[
 {t:4.5,frame:270,left:['ltg-wave0','ltg-ops-pr106-release-owner','ltg-ops-parity-host-ltg-self-gates','xl-cap-fillgeom-camera-lighting-authoring','xl-cap-drawing-reflection-glow-shadow','xl-cap-sparkline-preset-choices','ltg-max-m6-robustness'],right:['ltg-owner-xl','ltg-m6-fix-wolfxl-xlsx-render-png-crash','xl-lambda-parameter-validation','xl-cap-custom-geometry-editing-metadata','xl-x14-data-validations-read','ltg-ops-gate-host-verda-env-parity','ltg-owner-docx']},
 {t:11,frame:660,left:['ltg-m6-fix-wolfxl-xlsx-render-png-crash','ltg-owner-xl','ltg-ops-pr106-release-owner','xl-cap-fillgeom-camera-lighting-authoring','xl-cap-drawing-reflection-glow-shadow','xl-cap-sparkline-preset-choices','ltg-max-m6-robustness'],right:['ltg-wave0','ltg-ops-parity-host-ltg-self-gates','xl-lambda-parameter-validation','xl-cap-custom-geometry-editing-metadata','xl-x14-data-validations-read','ltg-ops-gate-host-verda-env-parity','ltg-owner-docx']}
];
