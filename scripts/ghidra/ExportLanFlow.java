import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import java.io.*;
import java.util.*;
public class ExportLanFlow extends GhidraScript {
 public void run() throws Exception {
  Set<String> names=new HashSet<>(Arrays.asList("ClientRoom::SendClientAlert","ClientRoom::processPlayerMessage","ClientRoomLAN::processPlayerMessage","ServerLAN::processPlayerMessage","RakNetLocalServer::processMessage","ClientRoom::reduceMagazine","ClientRoom::printWeaponStats","ClientRoom::sendWeaponEvent","WeaponStateObject::init","WeaponStateObject::reload","NetworkManager::sendWeaponCreate","WeaponManager::itemDrop","WeaponManager::itemTrack","Weapon::getWeaponStatus","LogWriter::logServerInfo","NetworkMessageDispatcher::getWeaponCreateData","WeaponManager::addItem","ClientRoom::updateWeaponTracking","ClientRoom::settleWeaponShotCounters","ClientRoomLAN::validateBallistics","ClientRoom::processPlayerLocation","ServerLAN::Update","ServerState::ProcessMessage","ServerState::Send","NetworkManager::sendDataMessageToAll","RakNetDelegate::processMessage","ServerState::sendToClient","ServerLAN::sendToClient"));
  if(getScriptArgs().length>1){names.clear();for(int i=1;i<getScriptArgs().length;i++)names.add(getScriptArgs()[i]);}
  PrintWriter w=new PrintWriter(new FileWriter(getScriptArgs()[0]));DecompInterface d=new DecompInterface();d.openProgram(currentProgram);
  FunctionIterator fs=currentProgram.getFunctionManager().getFunctions(true);
  while(fs.hasNext()){Function f=fs.next();String n=f.getSymbol().getName(true);if(!names.contains(n)||f.getEntryPoint().getOffset()<0x600000)continue;
   w.println("FUNCTION: "+n+" @ "+f.getEntryPoint());DecompileResults r=d.decompileFunction(f,90,monitor);if(r.getDecompiledFunction()!=null)w.println(r.getDecompiledFunction().getC());else w.println(r.getErrorMessage());w.flush();}
  w.close();d.dispose();
 }
}
