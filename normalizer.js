const aliases={
 headache:['headache','head ache','head pain','pain in my head','haedache','hedache','haed pain'],
 diarrhea:['diarrhea','diarrhoea','diarhea','loose motion','loose motions','loose stool','loose stools','motions'],
 vomiting:['vomiting','vomitting','throwing up','threw up','puking'],
 nausea:['nausea','nauseous','feel sick','queasy'],
 abdominal_pain:['stomach pain','stomach ache','stomack pain','belly pain','tummy pain','abdominal pain','abdomen pain'],
 fever:['fever','high temperature','temperature'], cough:['cough','coughing'], sore_throat:['sore throat','throat pain'],
 runny_nose:['runny nose','nose running'], blocked_nose:['blocked nose','stuffy nose','congested nose'],
 eye_pain:['eye pain','pain in my eye','eyes hurt'], eye_strain:['eye strain','tired eyes','strained eyes'],
 blurred_vision:['blurred vision','blurry vision'], dizziness:['dizziness','dizzy','lightheaded'],
 fatigue:['fatigue','tiredness','weakness','very tired','low energy'], chest_pain:['chest pain','pain in my chest'],
 breathing_difficulty:['difficulty breathing','shortness of breath','trouble breathing','breathless'],
 blood_stool:['blood in stool','bloody stool','blood in my stool'], blood_vomit:['blood in vomit','vomiting blood','blood when i throw up']
};
const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
export function normalize(text){const src=String(text||'').toLowerCase();const out=[];for(const [concept,words] of Object.entries(aliases)){for(const word of words){const re=new RegExp(`(^|[^a-z])${escape(word)}([^a-z]|$)`,'i');if(re.test(src)){out.push({concept,matched:word});break;}}if(!out.some(x=>x.concept===concept)){for(const word of words.filter(w=>w.includes(' '))){const parts=word.split(' ');if(parts.length===2&&parts[0].length>4){const close=(a,b)=>{if(Math.abs(a.length-b.length)>1)return false;let d=0,i=0,j=0;while(i<a.length&&j<b.length){if(a[i]===b[j]){i++;j++;}else{d++;if(d>1)return false;if(a.length>=b.length)i++;else j++;}}return d+(i<a.length||j<b.length?1:0)<=1;};if(parts.every(p=>src.split(/[^a-z]+/).some(t=>t===p||close(t,p)))){out.push({concept,matched:word,fuzzy:true});break;}}}}}return [...new Map(out.map(x=>[x.concept,x])).values()];}
export const label=c=>({abdominal_pain:'stomach / abdominal pain',blood_stool:'blood in stool',blood_vomit:'blood in vomit',breathing_difficulty:'breathing difficulty',eye_pain:'eye pain',eye_strain:'eye strain',sore_throat:'sore throat',runny_nose:'runny nose',blocked_nose:'blocked nose',blurred_vision:'blurred vision',chest_pain:'chest pain'}[c]||c.replaceAll('_',' '));
