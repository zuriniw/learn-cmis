import java.util.ArrayList;
import java.util.Collections;
import java.net.DatagramSocket;
import java.net.DatagramPacket;
import java.net.SocketException;
import java.io.IOException;

//these are variables you should leave alone
int index = 0; //starts at zero-ith trial
float border = 0; //some padding from the sides of window, set later
int trialCount = 5; //WILL BE MODIFIED FOR THE BAKEOFF
//int trialCount = 5 + (int)random(5);

//this will be set higher for the bakeoff
int trialIndex = 0; //what trial are we on
int errorCount = 0;  //used to keep track of errors
float errorPenalty = 1.0f; //for every error, add this value to mean time
int startTime = 0; // time starts when the first click is captured
int finishTime = 0; //records the time of the final click
boolean userDone = false; //is the user done

final int screenPPI = 72; //what is the DPI of the screen you are using
//you can test this by drawing a 72x72 pixel rectangle in code, and then confirming with a ruler it is 1x1 inch. 

//These variables are for my example design. Your input code should modify/replace these!
float logoX = 500;
float logoY = 500;
float logoZ = 50f;
float logoRotation = 0;
color logoColor = color(255); 


private class Destination
{
  float x = 0;
  float y = 0;
  float rotation = 0;
  float z = 0;
}

ArrayList<Destination> destinations = new ArrayList<Destination>();

// this setup function is executed once when the program starts
void setup() {
  size(1000, 800);  
  rectMode(CENTER);
  textFont(createFont("Arial", inchToPix(.3f))); //sets the font to Arial that is 0.3" tall
  textAlign(CENTER);
  rectMode(CENTER); //draw rectangles not from upper left, but from the center outwards
  
  //don't change this! 
  border = inchToPix(2f); //padding of 1.0 inches

  println("creating "+trialCount + " targets");
  for (int i=0; i<trialCount; i++) //don't change this! 
  {
    Destination d = new Destination();
    d.x = random(border, width-border); //set a random x with some padding
    d.y = random(border, height-border); //set a random y with some padding
    d.rotation = random(0, 360); //random rotation between 0 and 360
    int j = (int)random(20);
    d.z = ((j%5)+1)*inchToPix(.5f); //increasing size from .5 up to 5.0" 
    destinations.add(d);
    println("created target with " + d.x + "," + d.y + "," + d.rotation + "," + d.z);
  }

  Collections.shuffle(destinations); // randomize the order of the button; don't change this.
  
  // Start the UDP receiver thread on port 5005.
  new UDPReceiver(5005).start();
}

// this loop function is running continously after setup() is executed
void draw() {

  background(40); //background is dark grey
  fill(200);
  noStroke();
  
  //Test square in the top left corner. Should be 1 x 1 inch
  // rect(inchToPix(0.5), inchToPix(0.5), inchToPix(1), inchToPix(1));

  //you may not modify this printout code 
  if (userDone)
  {
    text("User completed " + trialCount + " trials", width/2, inchToPix(.4f));
    text("User had " + errorCount + " error(s)", width/2, inchToPix(.4f)*2);
    text("User took " + (finishTime-startTime)/1000f/trialCount + " sec per destination", width/2, inchToPix(.4f)*3);
    text("User took " + ((finishTime-startTime)/1000f/trialCount+(errorCount*errorPenalty)) + " sec per destination inc. penalty", width/2, inchToPix(.4f)*4);
    return;
  }

  //===========DRAW DESTINATION SQUARES=================
  for (int i=trialIndex; i<trialCount; i++) // reduces over time
  {
    pushMatrix();
    Destination d = destinations.get(i); //get destination trial
    translate(d.x, d.y); //center the drawing coordinates to the center of the destination trial
    
    rotate(radians(d.rotation)); //rotate around the origin of the Ddestination trial
    noFill();
    strokeWeight(3f);
    if (trialIndex==i)
      stroke(255, 0, 0, 192); //set color to semi translucent
    else
      stroke(128, 128, 128, 128); //set color to semi translucent
    rect(0, 0, d.z, d.z);
    popMatrix();
  }

  //===========DRAW LOGO SQUARE=================
  pushMatrix();
  translate(logoX, logoY);
  rotate(radians(logoRotation));
  noStroke();
  fill(logoColor);
  rect(0, 0, logoZ, logoZ);  // 绘制方块
  
  popMatrix();
  

  //===========DRAW EXAMPLE CONTROLS=================
  fill(255);
  scaffoldControlLogic(); //you may want to replace this!
  text("Trial " + (trialIndex+1) + " of " +trialCount, width/2, inchToPix(.8f));
}

//my example design for control, which is terrible
void scaffoldControlLogic()
{
  //upper left corner, rotate counterclockwise
  text("CCW", inchToPix(.4f), inchToPix(.4f));
  if (mousePressed && dist(0, 0, mouseX, mouseY)<inchToPix(.8f))
    logoRotation--;

  //upper right corner, rotate clockwise
  text("CW", width-inchToPix(.4f), inchToPix(.4f));
  if (mousePressed && dist(width, 0, mouseX, mouseY)<inchToPix(.8f))
    logoRotation++;

  //lower left corner, decrease Z
  text("-", inchToPix(.4f), height-inchToPix(.4f));
  if (mousePressed && dist(0, height, mouseX, mouseY)<inchToPix(.8f))

  //lower right corner, increase Z
  text("+", width-inchToPix(.4f), height-inchToPix(.4f));
  if (mousePressed && dist(width, height, mouseX, mouseY)<inchToPix(.8f))
    logoZ = constrain(logoZ+inchToPix(.02f), .01, inchToPix(4f)); //leave min and max alone! 

  //left middle, move left
  text("left", inchToPix(.4f), height/2);
  if (mousePressed && dist(0, height/2, mouseX, mouseY)<inchToPix(.8f))
    logoX-=inchToPix(.02f);

  text("right", width-inchToPix(.4f), height/2);
  if (mousePressed && dist(width, height/2, mouseX, mouseY)<inchToPix(.8f))
    logoX+=inchToPix(.02f);

  text("up", width/2, inchToPix(.4f));
  if (mousePressed && dist(width/2, 0, mouseX, mouseY)<inchToPix(.8f))
    logoY-=inchToPix(.02f);

  text("down", width/2, height-inchToPix(.4f));
  if (mousePressed && dist(width/2, height, mouseX, mouseY)<inchToPix(.8f))
    logoY+=inchToPix(.02f);
}





void mousePressed()
{
  if (startTime == 0) //start time on the instant of the first user click
  {
    startTime = millis();
    println("time started!");
  }
}

void mouseReleased()
{  
  //check to see if user clicked middle of screen within 3 inches, which this code uses as a submit button
  if (dist(width/2, height/2, mouseX, mouseY)<inchToPix(3f))
  {
    if (userDone==false && !checkForSuccess())
      errorCount++;

    trialIndex++; //and move on to next trial

    if (trialIndex==trialCount && userDone==false)
    {
      userDone = true;
      finishTime = millis();
    }
  }
}

// you may not change the error computation
public boolean checkForSuccess()
{
  Destination d = destinations.get(trialIndex);  
  boolean closeDist = dist(d.x, d.y, logoX, logoY) < inchToPix(.2f); //has to be within +-0.2"
  boolean closeRotation = calculateDifferenceBetweenAngles(d.rotation, logoRotation) <= 10;
  boolean closeZ = abs(d.z - logoZ) < inchToPix(.2f); //has to be within +-0.2"  

  println("Close Enough Distance: " + closeDist + " (logo X/Y = " + d.x + "/" + d.y + ", destination X/Y = " + logoX + "/" + logoY +")");
  println("Close Enough Rotation: " + closeRotation + " (rot dist="+calculateDifferenceBetweenAngles(d.rotation, logoRotation)+")");
  println("Close Enough Z: " +  closeZ + " (logo Z = " + d.z + ", destination Z = " + logoZ +")");
  println("Close enough all: " + (closeDist && closeRotation && closeZ));

  return closeDist && closeRotation && closeZ;
}

//utility function I include to calc diference between two angles
double calculateDifferenceBetweenAngles(float a1, float a2)
{
  double diff=abs(a1-a2);
  diff%=90;
  if (diff>45)
    return 90-diff;
  else
    return diff;
}

//utility function to convert inches into pixels based on screen PPI
float inchToPix(float inch)
{
  return inch*screenPPI;
}

// ----- UDP Receiver Thread -----
// This thread listens on the specified UDP port for incoming command strings.
class UDPReceiver extends Thread {
  DatagramSocket socket;
  
  UDPReceiver(int port) {
    try {
      socket = new DatagramSocket(port);
      println("UDP Receiver started on port " + port);
    } catch (SocketException e) {
      e.printStackTrace();
    }
  }
  
  public void run() {
    byte[] buffer = new byte[1024];
    while (true) {
      DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
      try {
        socket.receive(packet);
        String command = new String(packet.getData(), 0, packet.getLength()).trim();
        println("Received command: " + command);
        // Update the sketch state based on the command received.
        processCommand(command);
      } catch (IOException e) {
        e.printStackTrace();
      }
    }
  }
}

// ====== 新增键盘输入处理 ======
void keyPressed() {
  // 仅处理基本键（非特殊控制键）
  if (key != CODED) {
    // 将小写字母转为大写以匹配命令格式
    String cmd = String.valueOf(key).toUpperCase();
    processCommand(cmd);
  }
}

// ====== 新增轴方向变量 ======
float axisDirection = 0; // 独立控制移动方向（单位：度）

void processCommand(String cmd) {
  cmd = cmd.toUpperCase();
  float moveStep = inchToPix(.120f);

  switch(cmd) {
    // === 新的移动控制 ===
    case "U": 
      // 上升 (负Y方向)
      logoY -= moveStep;
      logoColor = color(0, 155, 100);
      break;
    case "D": 
      // 下降 (正Y方向)
      logoY += moveStep;
      logoColor = color(155, 0, 100);
      break;
    case "L":
      // 右移 (正X方向)
      logoX += moveStep;
      logoColor = color(100, 100, 155);
      break;
    case "A":
      // 左移 (负X方向)
      logoX -= moveStep;
      logoColor = color(155, 100, 100);
      break;
    case "M":
      // 右移 (正X方向)
      logoX += moveStep * 3;
      logoColor = color(100, 100, 155);
      break;
    case "Z":
      // 左移 (负X方向)
      logoX -= moveStep * 3;
      logoColor = color(155, 100, 100);
      break;

    // === 保留旋转控制 ===
    case "I":  // 逆时针
      logoRotation = (logoRotation - 8 + 360) % 360;
      break;
    case "O":  // 顺时针
      logoRotation = (logoRotation + 30) % 360;
      break;

    // === 其他保持原有逻辑 ===
    case "N":
      logoColor = color(255);   
      break;
    case "T": 
      logoZ = constrain(logoZ - inchToPix(.06f), .01, inchToPix(4f));
      break;
    case "Y":
      logoZ = constrain(logoZ + inchToPix(.06f), .01, inchToPix(4f)); 
      break;
    case "C":
      if (!userDone) {
        if (!checkForSuccess()) errorCount++;
        trialIndex++;
        if (trialIndex == trialCount) {
          userDone = true;
          finishTime = millis();
        }
      }
      break;
  }
}
