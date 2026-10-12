import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.address.*;
import java.io.*;
import java.util.*;
public class ExportLanNotification extends GhidraScript {
 public void run() throws Exception {
  PrintWriter w=new PrintWriter(new FileWriter(getScriptArgs()[0]));
  DecompInterface d=new DecompInterface();d.openProgram(currentProgram);
  LinkedHashSet<Function> chosen=new LinkedHashSet<>();
  long[] strings={0x108cc23L,0x108cc7dL,0x108cf08L,0x108d08dL,0x108d0dfL,0x108d174L,0x108d1d7L,0x108d2c0L,0x108d45bL,0x108d4dfL,0x108d546L,0x1089497L};
  for(long x:strings){Address a=toAddr(x+0x100000L);w.println("STRING "+a+" "+getDataAt(a));for(Reference r:getReferencesTo(a)){Function f=getFunctionContaining(r.getFromAddress());w.println("XREF "+r+" FUNCTION "+(f==null?"NONE":f.getSymbol().getName(true)));if(f!=null)chosen.add(f);}}
  for(String arg:getScriptArgs()){if(arg.startsWith("0x")){Function f=getFunctionContaining(toAddr(Long.decode(arg)));if(f!=null)chosen.add(f);}}
  LinkedHashSet<Function> roots=new LinkedHashSet<>(chosen);
  for(Function f:roots){w.println("CALLERS OF "+f.getSymbol().getName(true)+" "+f.getEntryPoint());for(Reference r:getReferencesTo(f.getEntryPoint())){Function c=getFunctionContaining(r.getFromAddress());w.println("CALLER "+r+" "+(c==null?"NONE":c.getSymbol().getName(true)));if(c!=null && r.getReferenceType().isCall())chosen.add(c);}}
  for(Function f:chosen){w.println("FUNCTION: "+f.getSymbol().getName(true)+" @ "+f.getEntryPoint()+" BODY "+f.getBody());DecompileResults r=d.decompileFunction(f,120,monitor);if(r.getDecompiledFunction()!=null)w.println(r.getDecompiledFunction().getC());else w.println(r.getErrorMessage());w.flush();}
  w.close();d.dispose();
 }
}
