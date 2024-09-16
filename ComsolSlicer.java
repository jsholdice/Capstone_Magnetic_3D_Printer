import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.File;

import java.util.*;

import com.comsol.acdc.a.r;
import com.comsol.model.*;
import com.comsol.model.dbmigration.v52a.ProblemMigrator.Solver;
import com.comsol.model.physics.*;
import com.comsol.model.util.*;
import java.util.regex.*;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVPrinter;


public class ComsolSlicer {
    public static void main(String[] args) {
        try {
            // Call the run method of selection_test_mod to retrieve the Model object
            ModelUtil.initStandalone(false);
            
            // initialize motor relevant data 
            double distancePerRev = 3.0e-3; 
            double stepsPerRev = 800.0; 
            double degreePerStep = 0.45;
            
            // run the comcol simulation file in directory 
            Model model = Summer_Grabber.run();
            
            // obtain corresponding domain (voxel) magnetization data 
            List<List<double[]>> magnetizationData = DomainMagnetizationFinder(model);

            // obtain corresponding domain (voxel) geometric data
            List<List<double[]>> geometricData = DomainPositionSizeFinder(model);

            List<List<double[]>> GeoMagData = GeomMagListCombiner(magnetizationData, geometricData);

            // sort domainPositionSizeList based on domain position data to organize list printable sequence
            List<List<double[]>> sortedGMData = PositionSorter(GeoMagData);

            // generate and export GM code 
            createGMCode(sortedGMData);

        } catch (Exception e) {
            System.out.println("Error occurred: " + e.getMessage());
            e.printStackTrace();
        } finally {
            ModelUtil.disconnect();
        }
    }

    public static void createGMCode(List<List<double[]>> GeoMagData, double distancePerRev, double stepsPerRev, double degreePerStep) {
        // initialize required steps for each motor
        int requiredSteps = 0;
 
        String filePath = "Summer_Grabber.csv";
        try {
            // intialize file writer to the csv
            FileWriter fileWriter = new FileWriter(filePath);

            // Create CSVPrinter object with CSVFormat
            CSVPrinter csvPrinter = new CSVPrinter(fileWriter, CSVFormat.DEFAULT);

            // Write headers to CSV
            csvPrinter.printRecord("X", "Y", "Z", "Top", "Bottom");

            // iterate through each domain data in the given list
            for (List<double[]> domainSubList : GeoMagData){
                // grab the domain position data
                double[] positionData = domainSubList.get(1);
                // iterate over x, y, z and calculate the number of motor revolutions to move to this position and the calc steps to pulse motor to get there
                for (double motorPosition : positionData){
                    double requiredRevs = motorPosition/distancePerRev;
                    requiredSteps = (int) (stepsPerRev * requiredRevs);
                    csvPrinter.print(requiredSteps);
                }
                // repeat for the domain magnetization data
                double[] magnetizationData = domainSubList.get(3);
                for (double motorAngle : magnetizationData){
                    requiredSteps = (int) (motorAngle/degreePerStep);
                    csvPrinter.print(requiredSteps);
                }
                csvPrinter.println();
            }
            csvPrinter.close();

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // sort domainPositionSizeList based on position data to organize based on print sequence
    public static List<List<double[]>> PositionSorter(List<List<double[]>> domainPositionSizeList) {
        // compare block domains based on the z value in the position list
        // we want to print bottom up 
        Comparator<List<double[]>> zLayer = Comparator.comparingDouble(sublist -> sublist.get(1)[2]);

        // then compare block domains based on the closest x/y value to the origin 
        // want to cure neirbouring voxels sequentially
        Comparator<List<double[]>> xyPlane = Comparator.comparingDouble(sublist -> {
            double[] secondElement = sublist.get(1);
            double x = secondElement[0];
            double y = secondElement[1];
            return Math.sqrt(x * x + y * y);
        });

        // Sort the domainPositionSizeList based on zLayer comparator and then xyPlane comparator
        domainPositionSizeList.sort(zLayer.thenComparing(xyPlane));

        return domainPositionSizeList;
    }


    // combine the magnetization domain data with the geometric domain data into one cumulative list
    public static List<List<double[]>> GeomMagListCombiner(List<List<double[]>> domainMagnetizationList, List<List<double[]>> domainPositionSizeList) {
        List<List<double[]>> cumulativeList = new ArrayList<>();

        // iterate through domainMagnetizationList manipulate domain sublists
        for (List<double[]> magnetizationSublist : domainMagnetizationList) {
            double[] firstElements = magnetizationSublist.get(0);
            // iterate over domain values in magnetizationList
            for (double value : firstElements) {
                // iterate through domainPositionSizeList and find the matching domain value 
                for (List<double[]> positionSizeSublist : domainPositionSizeList) {
                    if (positionSizeSublist.get(0)[0] == value) {
                        // append the magnetization data of the corresponding domain to the geometric data
                        List<double[]> newList = new ArrayList<>(positionSizeSublist);
                        newList.add(magnetizationSublist.get(1));
                        cumulativeList.add(newList);
                        break;
                    }
                }
            }
        }   
        return cumulativeList;
    }


    // returns the position and size for every domain 
    public static List<List<double[]>> DomainPositionSizeFinder(Model model) {
        List<String> blockFeatures = new ArrayList<>();
        // obtain a list of the geometric features in the model and iterate over them
        GeomFeatureList geometricFeatures = model.component("comp1").geom("geom1").feature();
        for (GeomFeature geoFeature: geometricFeatures){
            // obtain the tag and only store those that match the block tag
            String feature = geoFeature.tag();
            if(feature.contains("blk")) {
                blockFeatures.add(feature);
            }
        }
        System.out.println(blockFeatures);
        List<List<double[]>> domainPositionSizeList = new ArrayList<>();
        // iterate over every block feature and obtain the domain, position, and size data 
        for (String blk: blockFeatures){
            // must turn on sleection to obtain domain value
            model.component("comp1").geom("geom1").feature(blk).set("selresult", true);
            model.component("comp1").geom("geom1").feature(blk).set("selresultshow", "dom");
            System.out.println("Running...");
            model.component("comp1").geom("geom1").run();
            // obtain block value and convert to double array 
            int[] blkEntities = model.component("comp1").selection("geom1_"+ blk + "_dom").inputEntities();
            //obtain the last element of the blk entities to get the most recent domain and convert to double 
            double[] blkDomain = {(double) blkEntities[blkEntities.length-1]};

            // obtain the position and size value for the feature 
            double[] blkPosition = model.component("comp1").geom("geom1").feature(blk).getDoubleArray("pos");
            double[] blkSize = model.component("comp1").geom("geom1").feature(blk).getDoubleArray("size");

            // create a sub list containing the position and size for every domain 
            List<double[]> domainPositionSize = new ArrayList<>();
            domainPositionSize.add(blkDomain);
            domainPositionSize.add(blkPosition);
            domainPositionSize.add(blkSize);
            // for each feature and its corresponding domain store the position and size data 
            domainPositionSizeList.add(domainPositionSize);
        }
        return domainPositionSizeList;
    }


    public static List<List<double[]>> DomainMagnetizationFinder(Model model) {
        // initialize magnetic feature list that will store all the created magnetic physic features
        List<List<double[]>> domainMagnetizationList = new ArrayList<>();
        
        // obtain a list of all the mfnc physic features
        PhysicsFeatureList physicFeatures = model.component("comp1").physics("mfnc").feature();
        
        // iterate over all the features and store only those that contain the mfc tag and magnetization equations
        for (PhysicsFeature physFeature : physicFeatures) {
            String feature = physFeature.tag();
            
            // only use features that are related to magnetizations
            if (feature.contains("mfc")) {
                String featureEquation = model.component("comp1").physics("mfnc").feature(feature).getString("ConstitutiveRelationBH");
                // only use features related to magnetizations
                if (featureEquation.contains("Magnetization")){
                    String[] mValuesList = model.component("comp1").physics("mfnc").feature(feature).getStringArray("M");
                    // convert string array for the magnetization values into integer
                    double[] magnetizationValues = new double[mValuesList.length];
                    for (int i = 0; i < mValuesList.length; i++) {
                        magnetizationValues[i] = Integer.parseInt(mValuesList[i]);
                    }
                    // convert magnetization x, y, z into sphereical coordinates to use for motor rotations
                    double[] magnetRotations = cartesianToSpherical(magnetizationValues);
                    // obtain the number of domains assigned to the magnetization values
                    int[] domains = model.component("comp1").physics("mfnc").feature(feature).selection().entities();
                    // Iterate over domains array and add to domainMagnetizationList
                    for (int i = 0; i < domains.length; i++) {
                        List<double[]> domainMagnetizationPair = new ArrayList<>();
                        domainMagnetizationPair.add(new double[]{domains[i]});
                        domainMagnetizationPair.add(magnetRotations);
                        domainMagnetizationList.add(domainMagnetizationPair);
                    }
                }
            }
        }
        return domainMagnetizationList;
    }

     // Accepts magnetizations and converts it into normalized x,y,z 
    public static double[] cartesianToSpherical(double[] magnetizationValues) {
        // Convert Cartesian to Spherical coordinates
        double x = magnetizationValues[0];
        double y = magnetizationValues[1];
        double z = magnetizationValues[2];
        
        double r = Math.sqrt(x*x + y*y + z*z); // radial distance
        double theta = Math.toDegrees(Math.acos(z / r)); // inclination angle
        double phi = Math.toDegrees(Math.atan2(y, x)); // azimuth angle

        // recombine into normalized array
        double[] rotations = {theta, phi};
        return rotations;
    }
}
