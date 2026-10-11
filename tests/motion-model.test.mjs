import test from 'node:test';
import assert from 'node:assert/strict';
import {sampleAt,clockStep} from '../web/video-replica/motion-model.mjs';
test('exact sample preserves that frame and discrete observations, including endpoint',()=>{
 const rows=[{t:0,frame:0,camera:[1,0,0,1,0,0],parts:{},pointer:null},{t:.05,frame:3,camera:[1,0,0,1,1,1],parts:{},pointer:{source_xy:[20,30]}}];
 assert.equal(sampleAt(rows,.05).frame,3);
 assert.deepEqual(sampleAt(rows,.05).pointer,{source_xy:[20,30]});
 assert.equal(sampleAt(rows,100).frame,3);
});

test('seek interpolates observed transforms and never extrapolates duration',()=>{
 const rows=[{t:0,camera:[1,0,0,1,0,0]},{t:1,camera:[2,0,0,2,-20,-40]}];
 assert.deepEqual(sampleAt(rows,.5).camera,[1.5,0,0,1.5,-10,-20]);
 assert.equal(sampleAt(rows,5).t,1);
 assert.equal(sampleAt(rows,-1).t,0);
});
test('play reaches end without invented loop and pause freezes',()=>{
 assert.deepEqual(clockStep({time:14.9,playing:true},.5,15.133333),{time:15.133333,playing:false});
 assert.deepEqual(clockStep({time:8,playing:false},.5,15),{time:8,playing:false});
});
