export async function precisionArithmetic(api,request){
  return api.request("/calculation-engine/v1/precision",{method:"POST",body:request});
}
export async function precisionArithmeticCalculationObject(api,calculationObjectRequest,precisionArithmetic){
  return api.request("/calculation-engine/v1/precision/calculation-object",{
    method:"POST",body:{calculationObjectRequest,precisionArithmetic}});
}
